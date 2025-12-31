# titles/ AGENTS.md

Job Titles Management Module

## Module Overview

This module manages job titles. It has a simple tenant-aware CRUD structure.

**Core Features:**
- Job title CRUD operations
- Tenant-aware operations
- Unique title names (per tenant)
- Soft delete pattern
- Minimal business logic

**Dependencies:**
- `tenants` module (Tenant context)
- `utils` module (BaseModel, BaseService)

## Files Structure

```
titles/
├── __init__.py
├── apps.py
├── models.py              # Title model
├── serializers.py         # DRF serializers
├── services.py            # Business logic (TitleService)
├── views.py               # API views
└── tests/
    ├── test_services.py   # Service layer tests
    └── test_views.py      # API endpoint tests
```

## Key Components

### 1. Title Model (`models.py`)

Simple and minimal model structure.

```python
class Title(BaseModel):  # BaseModel: created_on, updated_on, attributes
    name = models.CharField(
        _("name"),
        max_length=255,
        unique=True,  # Unique within tenant
        db_index=True
    )
    is_active = models.BooleanField(_("is active"), default=True)
    
    class Meta:
        verbose_name = _("title")
        verbose_name_plural = _("titles")
    
    def __str__(self):
        return self.name
```

**Field Descriptions:**
- `name`: Title name (e.g., "Software Engineer", "HR Manager")
- `unique=True`: No duplicate titles within the same tenant
- `db_index=True`: Index for fast search
- `is_active`: Flag for soft delete

### 2. TitleService (`services.py`)

Minimal business logic, only basic CRUD.

```python
class TitleService(BaseService):
    def create_object(self, name: str, **kwargs) -> Title:
        """Creates a new title."""
        title = Title.objects.create(name=name, **kwargs)
        return title
    
    def update_object(self, instance: Title, **kwargs) -> Title:
        """Updates title."""
        for attr, value in kwargs.items():
            setattr(instance, attr, value)
        instance.save(update_fields=kwargs.keys())
        return instance
    
    def delete_object(self, instance: Title) -> None:
        """Performs soft delete on title."""
        instance.is_active = False
        instance.save(update_fields=["is_active"])
```

**Features:**
- ✅ Soft delete pattern (is_active=False)
- ✅ update_fields optimization
- ✅ Minimal, clean code
- ❌ No hard delete (security)

### 3. API Endpoints (`views.py`)

Standard ModelViewSet structure.

```python
GET    /api/titles/                    # List titles
POST   /api/titles/                    # Create title
GET    /api/titles/{id}/               # Title detail
PUT    /api/titles/{id}/               # Update title
PATCH  /api/titles/{id}/               # Partial update
DELETE /api/titles/{id}/               # Delete title (soft delete)
```

**Permissions:**
- Authenticated users: Full CRUD access
- Unauthenticated users: No access

### 4. ViewSet (`views.py`)

```python
class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.filter(is_active=True).order_by("name")
    serializer_class = TitleSerializer
    permission_classes = [IsAuthenticated]
    service_class = TitleService()
    
    def perform_create(self, serializer):
        serializer.instance = self.service_class.create_object(
            **serializer.validated_data
        )
    
    def perform_update(self, serializer):
        serializer.instance = self.service_class.update_object(
            instance=serializer.instance,
            **serializer.validated_data
        )
    
    def perform_destroy(self, instance):
        self.service_class.delete_object(instance)
```

## Common Patterns

### 1. Tenant-Aware Title Operations

```python
from django_tenants.utils import tenant_context
from tenants.models import Client
from titles.services import TitleService

tenant = Client.objects.get(schema_name="evilcorp")

with tenant_context(tenant):
    service = TitleService()
    
    # Create title
    title = service.create_object(name="Software Engineer")
    
    # List titles
    titles = Title.objects.filter(is_active=True)
    
    # Update title
    service.update_object(title, name="Senior Software Engineer")
    
    # Soft delete title
    service.delete_object(title)
```

### 2. Unique Constraint Handling

```python
from django.db import IntegrityError

try:
    title = service.create_object(name="Software Engineer")
except IntegrityError:
    # Title with same name already exists (unique constraint)
    print("This title already exists")
```

### 3. Active Titles Only

```python
# Get only active titles
active_titles = Title.objects.filter(is_active=True).order_by("name")

# All titles (including passive)
all_titles = Title.objects.all()

# ViewSet returns only active titles by default
queryset = Title.objects.filter(is_active=True).order_by("name")
```

### 4. Bulk Create Pattern

```python
# Create multiple titles
titles_to_create = [
    "Software Engineer",
    "Senior Software Engineer",
    "Engineering Manager",
    "CTO",
    "HR Manager",
    "HR Specialist"
]

with tenant_context(tenant):
    for title_name in titles_to_create:
        try:
            service.create_object(name=title_name)
        except IntegrityError:
            print(f"{title_name} already exists, skipping...")
```

### 5. Title Search and Filter

```python
# Search
titles = Title.objects.filter(name__icontains="engineer", is_active=True)

# Starts with specific letter
titles = Title.objects.filter(name__istartswith="s", is_active=True)

# Ordering
titles = Title.objects.filter(is_active=True).order_by("name")  # A-Z
titles = Title.objects.filter(is_active=True).order_by("-created_on")  # Newest to oldest
```

## Testing Guidelines

### Test Coverage Target: 95%

**Reasons for high coverage target:**
- ✅ Simple model structure
- ✅ Minimal business logic
- ✅ Low dependencies
- ✅ Easy to test

### Service Tests (`test_services.py`)

```python
from django_tenants.test.cases import TenantTestCase
from model_bakery import baker
from utils.tests.mixins import TenantTestCaseMixin
from titles.services import TitleService
from titles.models import Title

class TitleServiceTestCase(TenantTestCaseMixin, TenantTestCase):
    def setUp(self):
        super().setUp()
        self.service = TitleService()
    
    def test_create_object_success(self):
        """Should create title successfully"""
        title = self.service.create_object(name="Software Engineer")
        
        self.assertIsNotNone(title)
        self.assertEqual(title.name, "Software Engineer")
        self.assertTrue(title.is_active)
    
    def test_create_object_duplicate_name_raises_exception(self):
        """Should raise IntegrityError for duplicate name"""
        self.service.create_object(name="Software Engineer")
        
        with self.assertRaises(IntegrityError):
            self.service.create_object(name="Software Engineer")
    
    def test_update_object_success(self):
        """Should update title name"""
        title = baker.make("titles.Title", name="Engineer")
        
        updated_title = self.service.update_object(
            title, name="Senior Engineer"
        )
        
        self.assertEqual(updated_title.name, "Senior Engineer")
    
    def test_delete_object_soft_delete(self):
        """Should soft delete title"""
        title = baker.make("titles.Title", is_active=True)
        
        self.service.delete_object(title)
        
        title.refresh_from_db()
        self.assertFalse(title.is_active)
```

### View Tests (`test_views.py`)

```python
from django_tenants.test.cases import TenantTestCase
from utils.tests.mixins import AuthenticatedTenantTestMixin
from model_bakery import baker

class TitleViewSetTestCase(AuthenticatedTenantTestMixin, TenantTestCase):
    def setUp(self):
        super().setUp()
        self.authenticate_client()
    
    def test_list_success(self):
        """Should list all active titles"""
        baker.make("titles.Title", name="Title 1", is_active=True)
        baker.make("titles.Title", name="Title 2", is_active=True)
        baker.make("titles.Title", name="Title 3", is_active=False)  # Passive
        
        response = self.get("/api/titles/")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)  # Sadece aktif
    
    def test_create_success(self):
        """Should create title"""
        data = {"name": "Software Engineer"}
        
        response = self.post("/api/titles/", data)
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["name"], "Software Engineer")
    
    def test_create_duplicate_name_fails(self):
        """Should fail for duplicate name"""
        baker.make("titles.Title", name="Software Engineer")
        
        data = {"name": "Software Engineer"}
        response = self.post("/api/titles/", data)
        
        self.assertEqual(response.status_code, 400)
    
    def test_update_success(self):
        """Should update title"""
        title = baker.make("titles.Title", name="Engineer")
        
        data = {"name": "Senior Engineer"}
        response = self.patch(f"/api/titles/{title.id}/", data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Senior Engineer")
    
    def test_delete_success(self):
        """Should soft delete title"""
        title = baker.make("titles.Title", is_active=True)
        
        response = self.delete(f"/api/titles/{title.id}/")
        
        self.assertEqual(response.status_code, 204)
        
        title.refresh_from_db()
        self.assertFalse(title.is_active)
    
    def test_list_without_authentication_fails(self):
        """Should fail without authentication"""
        self.client.credentials()  # Remove credentials
        
        response = self.get("/api/titles/")
        
        self.assertEqual(response.status_code, 401)
```

## Common Tasks

### Adding a New Title Field

```python
# 1. Add field to model (models.py)
class Title(BaseModel):
    name = models.CharField(max_length=255, unique=True, db_index=True)
    is_active = models.BooleanField(default=True)
    
    # New field
    description = models.TextField(
        blank=True,
        help_text="Title description"
    )
    level = models.CharField(
        max_length=50,
        choices=[
            ("junior", "Junior"),
            ("mid", "Mid-Level"),
            ("senior", "Senior"),
            ("lead", "Lead"),
        ],
        blank=True
    )

# 2. Create and apply migration
uv run python manage.py makemigrations titles
uv run python manage.py migrate_schemas

# 3. Add to serializer (serializers.py)
class TitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Title
        fields = ["id", "name", "description", "level", "is_active", "created_on"]

# 4. Write test
def test_create_with_description(self):
    title = self.service.create_object(
        name="Software Engineer",
        description="Develops software applications",
        level="mid"
    )
    self.assertEqual(title.description, "Develops software applications")
```

### Adding Search/Filter Endpoint

```python
# views.py
from rest_framework.decorators import action
from rest_framework.response import Response

class TitleViewSet(viewsets.ModelViewSet):
    # ...
    
    @action(detail=False, methods=["get"])
    def search(self, request):
        """
        Search titles.
        
        Query params:
        - q: Search term (searches in name)
        """
        query = request.query_params.get("q", "")
        
        titles = Title.objects.filter(
            name__icontains=query,
            is_active=True
        ).order_by("name")
        
        serializer = self.get_serializer(titles, many=True)
        return Response(serializer.data)

# Usage
# GET /api/titles/search/?q=engineer
```

### Bulk Operations

```python
# views.py
from rest_framework import status

class TitleViewSet(viewsets.ModelViewSet):
    # ...
    
    @action(detail=False, methods=["post"])
    def bulk_create(self, request):
        """
        Create multiple titles.
        
        Request body:
        {
            "titles": ["Title 1", "Title 2", "Title 3"]
        }
        """
        titles_list = request.data.get("titles", [])
        created_titles = []
        errors = []
        
        for title_name in titles_list:
            try:
                title = self.service_class.create_object(name=title_name)
                created_titles.append(title)
            except IntegrityError:
                errors.append(f"{title_name} already exists")
        
        return Response({
            "created": len(created_titles),
            "errors": errors
        }, status=status.HTTP_201_CREATED)

# Usage
# POST /api/titles/bulk_create/
# {"titles": ["Software Engineer", "HR Manager", "Designer"]}
```

## Security Considerations

### 1. Unique Constraint

```python
# Her tenant'ta aynı title name sadece bir kez
# Database level constraint
name = models.CharField(max_length=255, unique=True)
```

### 2. Tenant Isolation

```python
# ❌ WRONG: Creating title in public schema
title = Title.objects.create(name="Engineer")  # Error

# ✅ CORRECT: Within tenant context
with tenant_context(tenant):
    title = Title.objects.create(name="Engineer")
```

### 3. Soft Delete Only

```python
# No hard delete, only soft delete
def delete_object(self, instance: Title) -> None:
    instance.is_active = False  # Prevents data loss
    instance.save(update_fields=["is_active"])
```

### 4. Authentication Required

```python
# All endpoints require authentication
permission_classes = [IsAuthenticated]
```

## Common Pitfalls

### ❌ WRONG: Operating outside tenant context

```python
title = Title.objects.create(name="Engineer")  # DoesNotExist
```

### ✅ CORRECT: Use tenant context

```python
with tenant_context(tenant):
    title = Title.objects.create(name="Engineer")
```

### ❌ WRONG: Creating without duplicate name check

```python
title = Title.objects.create(name="Engineer")  # IntegrityError
```

### ✅ CORRECT: Use try-except

```python
try:
    title = Title.objects.create(name="Engineer")
except IntegrityError:
    # Handle duplicate
    pass
```

### ❌ WRONG: Hard delete

```python
title.delete()  # Data loss
```

### ✅ CORRECT: Soft delete

```python
service.delete_object(title)  # is_active=False
```

## Quick Commands

```bash
# Run tests
uv run python manage.py test titles

# Coverage ile test (Target: 95%)
uv run coverage run --source=titles manage.py test titles
uv run coverage report -m

# Belirli bir test
uv run python manage.py test titles.tests.test_services.TitleServiceTestCase.test_create_object_success

# Create migration
uv run python manage.py makemigrations titles

# Migration uygula (tenant-aware)
uv run python manage.py migrate_schemas

# Django shell'de test
uv run python manage.py shell
>>> from django_tenants.utils import tenant_context
>>> from tenants.models import Client
>>> from titles.models import Title
>>> tenant = Client.objects.get(schema_name="test")
>>> with tenant_context(tenant):
...     titles = Title.objects.all()
...     print(f"Total titles: {titles.count()}")
```

## Dependencies

This module depends on:

- **tenants:** Client model (tenant context)
- **utils:** BaseModel, BaseService

Modules that use this module:

- **employees:** (Future) Titles can be assigned to employees

## Future Enhancements

Planned features:

1. **Employee-Title Relationship:**
```python
class Employee(BaseModel):
    # ...
    title = models.ForeignKey(Title, on_delete=models.SET_NULL, null=True)
```

2. **Title Hierarchy:**
```python
class Title(BaseModel):
    # ...
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True)
    level = models.IntegerField(default=1)  # Career progression
```

3. **Title Templates:**
```python
# Predefined common titles
COMMON_TITLES = [
    "Software Engineer",
    "Senior Software Engineer",
    "Engineering Manager",
    "CTO",
    # ...
]
```

## API Schema

Automatic API documentation:

```bash
# Swagger UI
http://localhost:8000/api/schema/swagger-ui/#/titles

# ReDoc
http://localhost:8000/api/schema/redoc/#tag/titles
```

---

**Coverage Target:** 95%
**Last Updated:** 2025-10-26
