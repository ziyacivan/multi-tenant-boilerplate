# employees/ AGENTS.md

Employee Management Module

## Module Overview

This module provides employee management functionality. Each tenant manages its own employees (tenant-aware).

**Core Features:**
- Employee CRUD operations
- Role-based permissions (employee, manager, owner)
- Personal details management
- Photo upload (ImageField)
- Soft delete pattern
- Tenant-aware operations

**Dependencies:**
- `users` module (User model - OneToOne relationship)
- `tenants` module (Tenant context)
- `utils` module (BaseModel, BaseService)

## Files Structure

```
employees/
├── __init__.py
├── apps.py
├── choices.py             # EmployeeRole, EmployeeGender enums
├── exceptions.py          # Employee-specific exceptions
├── mixins.py              # Permission mixins
├── models.py              # Employee, PersonalDetail models
├── permissions.py         # IsMinimumManagerOrReadOnly
├── serializers.py         # DRF serializers
├── services.py            # Business logic (EmployeeService)
├── views.py               # API views
└── tests/
    ├── test_services.py   # Service layer tests
    └── test_views.py      # API endpoint tests
```

## Key Components

### 1. Models (`models.py`)

**Employee Model:**
```python
class Employee(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    photo = models.ImageField(upload_to="employees/photos/", null=True, blank=True)
    role = models.CharField(
        max_length=20,
        choices=EmployeeRole.choices,
        default=EmployeeRole.employee
    )
    gender = models.CharField(
        max_length=20,
        choices=EmployeeGender.choices,
        default=EmployeeGender.male,
        null=True, blank=True
    )
    is_active = models.BooleanField(default=True)
    
    @property
    def email(self):
        return self.user.email
```

**PersonalDetail Model:**
```python
class PersonalDetail(BaseModel):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE)
    address = models.CharField(max_length=255, null=True, blank=True)
    identification_number = models.CharField(max_length=11, unique=True, ...)
    date_of_birth = models.DateField(null=True, blank=True)
    personal_phone = models.CharField(max_length=20, unique=True, ...)
    is_married = models.BooleanField(default=False)
    number_of_children = models.PositiveSmallIntegerField(default=0)
    graduation = models.CharField(max_length=255, null=True, blank=True)
    mandatory_military_service_completed = models.BooleanField(default=False)
    driver_license = models.CharField(max_length=20, null=True, blank=True)
    disability_degree = models.PositiveSmallIntegerField(null=True, blank=True)
    # Emergency contacts
    first_emergency_contact_name = models.CharField(...)
    first_emergency_contact_phone = models.CharField(...)
    second_emergency_contact_name = models.CharField(...)
    second_emergency_contact_phone = models.CharField(...)
    # Payroll info
    payroll_bank_account_no = models.CharField(...)
    payroll_bank_account_iban = models.CharField(max_length=34, unique=True, ...)
    payroll_bank_account_currency = models.CharField(max_length=3, ...)
```

### 2. Role System (`choices.py`)

```python
class EmployeeRole(models.TextChoices):
    employee = "employee", _("Employee")
    manager = "manager", _("Manager")
    owner = "owner", _("Owner")

class EmployeeGender(models.TextChoices):
    male = "male", _("Male")
    female = "female", _("Female")
    other = "other", _("Other")
```

**Role Hierarchy:**
- **owner:** Company owner (tenant owner), cannot be deleted
- **manager:** Manager, can perform employee CRUD operations
- **employee:** Regular employee, read-only access

### 3. EmployeeService (`services.py`)

**Methods:**
```python
def create_object(user, first_name, last_name, **kwargs) -> Employee
    # Create new employee
    # If user=None, automatically creates user (unverified)

def update_object(instance, **kwargs) -> Employee
    # Update employee (is_active cannot be updated)

def delete_object(instance, force_delete=False) -> None
    # Soft delete (is_active=False) or hard delete
    # Owner cannot be deleted (CannotDeleteEmployeeException)

def get_employee_by_user(user) -> Employee
    # Find employee by user

def get_personal_detail(employee) -> PersonalDetail | None
    # Get employee's personal details

def create_or_update_personal_detail(employee, **kwargs) -> PersonalDetail
    # Create or update personal details (get_or_create pattern)
```

### 4. Permissions (`permissions.py`)

```python
class IsMinimumManagerOrReadOnly(permissions.BasePermission):
    """
    - GET, HEAD, OPTIONS: Her authenticated user
    - POST, PUT, PATCH, DELETE: Sadece manager veya owner
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Write operations için manager veya owner olmalı
        employee = Employee.objects.get(user=request.user)
        return employee.role in [EmployeeRole.manager, EmployeeRole.owner]
```

### 5. API Endpoints (`views.py`)

```python
GET    /api/employees/                    # List employees
POST   /api/employees/                    # Create employee (manager+)
GET    /api/employees/{id}/               # Employee detail
PUT    /api/employees/{id}/               # Update employee (manager+)
PATCH  /api/employees/{id}/               # Partial update (manager+)
DELETE /api/employees/{id}/               # Delete employee (manager+)
GET    /api/employees/me/                 # Authenticated user's employee record
GET    /api/employees/{id}/personal-detail/  # Personal detail
POST   /api/employees/{id}/personal-detail/  # Create/update personal detail
```

**Permission Matrix:**
| Endpoint | Employee | Manager | Owner |
|----------|----------|---------|-------|
| GET (list/detail) | ✅ | ✅ | ✅ |
| POST (create) | ❌ | ✅ | ✅ |
| PUT/PATCH (update) | ❌ | ✅ | ✅ |
| DELETE | ❌ | ✅ (except owner) | ✅ (except owner) |

## Common Patterns

### 1. Tenant-Aware Employee Creation

```python
# ✅ CORRECT: Within tenant context
from django_tenants.utils import tenant_context
from tenants.models import Client

tenant = Client.objects.get(schema_name="evilcorp")

with tenant_context(tenant):
    service = EmployeeService()
    employee = service.create_object(
        user=user,
        first_name="John",
        last_name="Doe",
        role=EmployeeRole.manager
    )
```

### 2. Creating Employee Without User

```python
# Service automatically creates user
employee = service.create_object(
    email="newemployee@company.com",  # email required when user=None
    first_name="Jane",
    last_name="Smith"
)
# Created user:
# - email: newemployee@company.com
# - is_verified: False
# - is_active: False (default)
# - Unusable password (password reset required)
```

### 3. Soft Delete Pattern

```python
# Soft delete (default)
service.delete_object(employee, force_delete=False)
# employee.is_active = False
# employee.user.is_active = False

# Hard delete (force)
service.delete_object(employee, force_delete=True)
# employee and user completely deleted
# ⚠️ Owner can never be deleted
```

### 4. Personal Detail Management

```python
# Get or create pattern
personal_detail = service.create_or_update_personal_detail(
    employee=employee,
    identification_number="12345678901",
    date_of_birth=date(1990, 1, 1),
    address="123 Main St",
    is_married=True,
    number_of_children=2,
    payroll_bank_account_iban="TR123456789012345678901234"
)

# Returns None if personal detail doesn't exist
existing_detail = service.get_personal_detail(employee)
```

### 5. Role-Based Operations

```python
# Permission check in view
class EmployeeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsMinimumManagerOrReadOnly]
    
    def perform_create(self, serializer):
        # Can be called by manager or owner
        serializer.instance = self.service_class.create_object(
            **serializer.validated_data
        )
    
    @action(detail=False, methods=["get"])
    def me(self, request):
        # Authenticated user'ın kendi employee kaydı
        employee = self.service_class.get_employee_by_user(request.user)
        serializer = self.get_serializer(employee)
        return Response(serializer.data)
```

## Testing Guidelines

### Test Coverage Target: 80%

### Service Tests (`test_services.py`)

```python
from django_tenants.test.cases import TenantTestCase
from model_bakery import baker
from utils.tests.mixins import TenantTestCaseMixin
from employees.services import EmployeeService
from employees.choices import EmployeeRole

class EmployeeServiceTestCase(TenantTestCaseMixin, TenantTestCase):
    def setUp(self):
        super().setUp()
        self.service = EmployeeService()
    
    def test_create_object_success(self):
        """Should create employee with user"""
        user = baker.make("users.User")
        
        employee = self.service.create_object(
            user=user,
            first_name="John",
            last_name="Doe",
            role=EmployeeRole.employee
        )
        
        self.assertIsNotNone(employee)
        self.assertEqual(employee.user, user)
        self.assertEqual(employee.first_name, "John")
    
    def test_delete_object_owner_raises_exception(self):
        """Should not delete owner"""
        owner_employee = baker.make(
            "employees.Employee",
            role=EmployeeRole.owner
        )
        
        with self.assertRaises(CannotDeleteEmployeeException):
            self.service.delete_object(owner_employee, force_delete=False)
    
    def test_create_or_update_personal_detail(self):
        """Should create or update personal detail"""
        employee = baker.make("employees.Employee")
        
        personal_detail = self.service.create_or_update_personal_detail(
            employee=employee,
            identification_number="12345678901",
            date_of_birth=date(1990, 1, 1)
        )
        
        self.assertIsNotNone(personal_detail)
        self.assertEqual(personal_detail.identification_number, "12345678901")
```

### View Tests (`test_views.py`)

```python
from django_tenants.test.cases import TenantTestCase
from utils.tests.mixins import AuthenticatedTenantTestMixin
from employees.choices import EmployeeRole

class EmployeeViewSetTestCase(AuthenticatedTenantTestMixin, TenantTestCase):
    def setUp(self):
        super().setUp()
        # Manager olarak authenticate
        self.authenticate_client(role=EmployeeRole.manager)
    
    def test_list_success(self):
        """Manager should list all employees"""
        response = self.get("/api/employees/")
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("results", response.data)
    
    def test_create_as_manager_success(self):
        """Manager should create employee"""
        data = {
            "email": "newemployee@test.com",
            "first_name": "Jane",
            "last_name": "Doe",
            "role": EmployeeRole.employee
        }
        
        response = self.post("/api/employees/", data)
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["email"], "newemployee@test.com")
    
    def test_create_as_regular_employee_forbidden(self):
        """Regular employee cannot create employee"""
        self.authenticate_client(role=EmployeeRole.employee)
        
        data = {
            "email": "newemployee@test.com",
            "first_name": "Jane",
            "last_name": "Doe"
        }
        
        response = self.post("/api/employees/", data)
        
        self.assertEqual(response.status_code, 403)
```

## Common Tasks

### Adding a New Employee Field

```python
# 1. Add field to model (models.py)
class Employee(BaseModel):
    # ...
    department = models.CharField(
        _("department"),
        max_length=100,
        null=True,
        blank=True
    )

# 2. Create and apply migration
uv run python manage.py makemigrations employees
uv run python manage.py migrate_schemas

# 3. Add to serializer (serializers.py)
class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = [..., "department"]

# 4. Write test
def test_create_with_department(self):
    employee = self.service.create_object(
        user=user,
        first_name="John",
        last_name="Doe",
        department="Engineering"
    )
    self.assertEqual(employee.department, "Engineering")
```

### Adding a New Custom Action

```python
# views.py
from rest_framework.decorators import action

class EmployeeViewSet(viewsets.ModelViewSet):
    # ...
    
    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        """
        Activates the employee.
        
        Only manager or owner can use this.
        """
        employee = self.get_object()
        employee.is_active = True
        employee.user.is_active = True
        employee.user.save(update_fields=["is_active"])
        employee.save(update_fields=["is_active"])
        
        serializer = self.get_serializer(employee)
        return Response(serializer.data)

# Usage
# POST /api/employees/{id}/activate/
```

### Query Optimization (N+1 Prevention)

```python
# ❌ WRONG: N+1 query problem
class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    # Separate user query runs for each employee

# ✅ CORRECT: Use select_related
class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.select_related('user').all()
    # Users fetched in single query
    
    def get_queryset(self):
        return Employee.objects.select_related('user').filter(is_active=True)
```

## Security Considerations

### 1. Owner Protection

```python
# Owner can never be deleted
def delete_object(self, instance: Employee, force_delete: bool | None):
    if instance.role == EmployeeRole.owner:
        raise CannotDeleteEmployeeException()
    # ...
```

### 2. is_active Field Protection

```python
# is_active field cannot be updated (in service layer)
def update_object(self, instance: Employee, **kwargs):
    kwargs.pop("is_active", None)  # Remove is_active
    # Only activate/deactivate actions should be used
```

### 3. Tenant Isolation

```python
# ❌ WRONG: Query outside tenant context
employees = Employee.objects.all()  # Error or wrong data

# ✅ CORRECT: Within tenant context
with tenant_context(tenant):
    employees = Employee.objects.all()  # Tenant's employees
```

### 4. Photo Upload Security

```python
# Photo upload path: employees/photos/
# Pillow library validation (settings: IMAGE_UPLOAD_MAX_SIZE)
photo = models.ImageField(upload_to="employees/photos/", ...)
```

## Common Pitfalls

### ❌ WRONG: Creating employee in public schema

```python
employee = Employee.objects.create(...)  # DoesNotExist error
```

### ✅ CORRECT: Use tenant context

```python
with tenant_context(tenant):
    employee = Employee.objects.create(...)
```

### ❌ WRONG: Attempting to delete owner

```python
service.delete_object(owner_employee)  # CannotDeleteEmployeeException
```

### ✅ CORRECT: Check role

```python
if employee.role != EmployeeRole.owner:
    service.delete_object(employee)
```

### ❌ WRONG: Direct access to personal detail

```python
personal_detail = employee.personaldetail  # May raise DoesNotExist error
```

### ✅ CORRECT: Use service method

```python
personal_detail = service.get_personal_detail(employee)  # Returns None
```

## Quick Commands

```bash
# Run tests
uv run python manage.py test employees

# Test with coverage
uv run coverage run --source=employees manage.py test employees
uv run coverage report -m

# Specific test
uv run python manage.py test employees.tests.test_services.EmployeeServiceTestCase.test_create_object_success

# Create migration
uv run python manage.py makemigrations employees

# Apply migration (tenant-aware)
uv run python manage.py migrate_schemas

# Test in Django shell
uv run python manage.py shell
>>> from django_tenants.utils import tenant_context
>>> from tenants.models import Client
>>> from employees.services import EmployeeService
>>> tenant = Client.objects.get(schema_name="test")
>>> with tenant_context(tenant):
...     service = EmployeeService()
...     employees = Employee.objects.all()
```

## Dependencies

This module depends on:

- **users:** User model (OneToOne relationship)
- **tenants:** Client model (tenant context)
- **utils:** BaseModel, BaseService, custom exceptions

Modules that use this module:

- **tenants:** Owner employee created when tenant is created
- **titles:** Titles can be assigned to employees (future feature)

## API Schema

Automatic API documentation:

```bash
# Swagger UI
http://localhost:8000/api/schema/swagger-ui/#/employees

# ReDoc
http://localhost:8000/api/schema/redoc/#tag/employees
```

---

**Coverage Target:** 80%
**Last Updated:** 2025-10-26
