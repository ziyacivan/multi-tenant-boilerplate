# tenants/ AGENTS.md

Multi-Tenant Management Module

## Module Overview

This module is the core of the multi-tenant architecture. Each company is managed as a tenant and operates in its own schema.

**Core Features:**
- Tenant (company) CRUD operations
- Schema-per-tenant isolation
- Domain routing (subdomain support)
- Owner assignment
- Soft delete pattern (deactivate)
- Custom middleware (CustomTenantMiddleware)

**Dependencies:**
- `django-tenants` library
- `tenant-users` library
- `users` module (User model)
- `employees` module (Create owner employee)
- `utils` module (BaseModel, BaseService)

## Files Structure

```
tenants/
├── __init__.py
├── apps.py
├── exceptions.py          # Tenant-specific exceptions
├── middleware.py          # CustomTenantMiddleware
├── models.py              # Client, Domain models
├── serializers.py         # DRF serializers
├── services.py            # Business logic (ClientService)
├── views.py               # API views
└── management/
    └── commands/
        └── ...            # Custom management commands
```

## Key Components

### 1. Models (`models.py`)

**Client Model (Tenant):**
```python
class Client(BaseModel, TenantBase):
    # Basic info
    name = models.CharField(_("name"), max_length=255)  # Company name
    description = models.TextField(_("description"), blank=True)
    
    # Legal info
    legal_name = models.CharField(_("legal name"), max_length=255, blank=True)
    tax_no = models.CharField(_("tax number"), max_length=255, blank=True)
    tax_office = models.CharField(_("tax office"), max_length=255, blank=True)
    
    # Address info
    address = models.TextField(_("address"), blank=True)
    invoice_address = models.TextField(_("invoice address"), blank=True)
    city = models.CharField(_("city"), max_length=255, blank=True)
    country = models.CharField(_("country"), max_length=255, blank=True)
    
    # Contact info
    invoice_email_address = models.EmailField(_("invoice email address"), blank=True)
    short_name = models.CharField(_("short name"), max_length=255, blank=True)
    
    is_active = models.BooleanField(_("is active"), default=True)
    
    # django-tenants settings
    auto_create_schema = True   # Auto create schema
    auto_drop_schema = False    # Don't auto drop schema
```

**Domain Model:**
```python
class Domain(DomainMixin):
    pass  # DomainMixin'den inherit edilir
    # tenant (ForeignKey to Client)
    # domain (CharField, unique)
    # is_primary (BooleanField)
```

### 2. ClientService (`services.py`)

**Metodlar:**
```python
@transaction.atomic
def create_object(
    name, description, slug, owner,
    legal_name, tax_no, tax_office, address,
    invoice_address, city, country,
    invoice_email_address, short_name, **kwargs
) -> Client
    # Create new tenant (company)
    # 1. Create schema with provision_tenant()
    # 2. Update tenant information
    # 3. Add owner as employee

def update_object(instance, **kwargs) -> Client
    # Update tenant
    # ⚠️ name, slug, owner cannot be updated

def delete_object(instance) -> None
    # Soft delete (tenant deactivate)
    # 1. Deactivate all tenant users
    # 2. Add timestamp prefix to domain
    # 3. is_active=False

def active_client(instance) -> Client
    # Reactivate deactivated tenant
    # 1. Remove timestamp from domain
    # 2. Activate all users
    # 3. is_active=True
```

### 3. CustomTenantMiddleware (`middleware.py`)

Custom middleware for domain-based routing.

```python
class CustomTenantMiddleware(TenantMainMiddleware):
    """
    Tenant routing logic:
    1. Extract hostname from request
    2. Find tenant by domain
    3. Set schema
    4. Add tenant to request
    """
```

**Routing Flow:**
```
Request -> CustomTenantMiddleware -> Tenant Found -> Set Schema -> View
                                   -> Tenant Not Found -> Public Schema -> View
```

### 4. Schema Types

**Public Schema (shared):**
- Schema name: `public`
- Apps: `tenants`, `users`
- Shared by all tenants
- Domain: `localhost` (development)

**Tenant Schema:**
- Schema name: `{slug}` (example: `evilcorp`)
- Apps: `employees`, `titles`
- Each tenant has its own schema
- Domain: `{slug}.domain.com` or custom domain

### 5. API Endpoints (`views.py`)

```python
POST   /public/tenants/               # Create new tenant (company)
GET    /api/tenants/                  # List tenants (admin only)
GET    /api/tenants/{id}/             # Tenant detail
PUT    /api/tenants/{id}/             # Update tenant
PATCH  /api/tenants/{id}/             # Partial update
DELETE /api/tenants/{id}/             # Deactivate tenant (soft delete)
```

## Common Patterns

### 1. Creating a New Tenant

```python
from tenants.services import ClientService
from users.models import User

# 1. Create owner user
owner = User.objects.create_user(
    email="owner@company.com",
    password="secure_password",
    is_staff=True  # Tenant owner must be staff
)

# 2. Create tenant
service = ClientService()
tenant = service.create_object(
    name="Evil Corp",
    slug="evilcorp",  # Schema name and domain prefix
    owner=owner,
    description="A fictional company",
    legal_name="Evil Corporation Inc.",
    tax_no="1234567890",
    tax_office="Istanbul Tax Office",
    address="123 Main St, Istanbul",
    invoice_address="123 Main St, Istanbul",
    city="Istanbul",
    country="Turkey",
    invoice_email_address="billing@evilcorp.com",
    short_name="EvilCorp"
)

# Automatically:
# - evilcorp schema created
# - evilcorp.localhost domain added (development)
# - Owner added as employee (role=owner)
# - Migrations applied to tenant schema
```

### 2. Using Tenant Context

```python
from django_tenants.utils import tenant_context, schema_context
from tenants.models import Client

# Method 1: tenant_context (with tenant object)
tenant = Client.objects.get(schema_name="evilcorp")

with tenant_context(tenant):
    # All ORM queries within this block run in evilcorp schema
    employees = Employee.objects.all()
    print(f"Tenant: {tenant.name}, Employees: {employees.count()}")

# Method 2: schema_context (with schema name)
with schema_context("evilcorp"):
    employees = Employee.objects.all()

# ⚠️ Warning: Cannot access tenant models outside context
# employees = Employee.objects.all()  # DoesNotExist error
```

### 3. Tenant Deactivation (Soft Delete)

```python
# Soft delete
service = ClientService()
service.delete_object(tenant)

# Result:
# - tenant.is_active = False
# - tenant.domain_url = "1635789012-123-evilcorp.localhost" (timestamp prefix)
# - All tenant users is_active=False
# - Schema not deleted (auto_drop_schema=False)

# Reactivation
service.active_client(tenant)

# Result:
# - tenant.is_active = True
# - tenant.domain_url = "evilcorp.localhost" (timestamp removed)
# - All tenant users is_active=True
```

### 4. provision_tenant() Flow

```python
from tenant_users.tenants.tasks import provision_tenant

# provision_tenant() does:
# 1. Create Client object (name, slug)
# 2. Create schema (CREATE SCHEMA {slug})
# 3. Apply migrations (migrate_schemas)
# 4. Create domain ({slug}.domain.com)
# 5. Link owner to tenant
# 6. Give owner tenant permissions (is_staff, is_superuser)

tenant, domain = provision_tenant(
    tenant_name="Evil Corp",
    tenant_slug="evilcorp",
    owner=owner_user,
    is_staff=True,
    is_superuser=True
)
```

### 5. Multi-Tenant Query Patterns

```python
# In public schema (shared apps)
from django_tenants.utils import schema_context

with schema_context("public"):
    all_tenants = Client.objects.all()
    all_users = User.objects.all()

# In tenant schema (tenant apps)
with schema_context("evilcorp"):
    employees = Employee.objects.all()
    titles = Title.objects.all()

# ❌ WRONG: Accessing tenant model in public schema
employees = Employee.objects.all()  # DoesNotExist

# ✅ CORRECT: Use tenant context
with tenant_context(tenant):
    employees = Employee.objects.all()
```

## Testing Guidelines

### Test Coverage Target: 80%

### Tenant Test Setup

```python
from django_tenants.test.cases import TenantTestCase
from django_tenants.utils import get_public_schema_name
from tenants.models import Client, Domain

class TenantServiceTestCase(TenantTestCase):
    @classmethod
    def setUpClass(cls):
        # Public tenant'ı oluştur (sistem tenant'ı)
        super().setUpClass()
    
    def setUp(self):
        super().setUp()
        # Test tenant otomatik oluşturulur
        # cls.tenant -> Test tenant
        # cls.domain -> Test domain
```

### Service Tests

```python
from django_tenants.test.cases import TenantTestCase
from model_bakery import baker
from tenants.services import ClientService

class ClientServiceTestCase(TenantTestCase):
    def setUp(self):
        super().setUp()
        self.service = ClientService()
    
    def test_create_object_success(self):
        """Should create tenant with schema"""
        owner = baker.make("users.User", is_staff=True)
        
        tenant = self.service.create_object(
            name="Test Company",
            slug="testco",
            owner=owner,
            description="Test",
            legal_name="Test Company Ltd.",
            tax_no="1234567890",
            tax_office="Test Office",
            address="Test Address",
            invoice_address="Test Invoice Address",
            city="Test City",
            country="Test Country",
            invoice_email_address="billing@test.com",
            short_name="TestCo"
        )
        
        self.assertIsNotNone(tenant)
        self.assertEqual(tenant.slug, "testco")
        self.assertEqual(tenant.owner, owner)
        
        # Schema oluşturuldu mu?
        self.assertTrue(
            Client.objects.filter(schema_name="testco").exists()
        )
    
    def test_delete_object_soft_delete(self):
        """Should soft delete tenant"""
        tenant = baker.make("tenants.Client", is_active=True)
        
        self.service.delete_object(tenant)
        
        tenant.refresh_from_db()
        self.assertFalse(tenant.is_active)
        self.assertIn("-", tenant.domain_url)  # Timestamp prefix
```

## Common Tasks

### Yeni Bir Tenant Field Eklemek

```python
# 1. Model'e field ekle (models.py)
class Client(BaseModel, TenantBase):
    # ...
    phone_number = models.CharField(
        _("telefon numarası"),
        max_length=20,
        blank=True
    )

# 2. Create and apply migration
# ⚠️ Warning: tenants is shared app, migrate only with --shared
uv run python manage.py makemigrations tenants
uv run python manage.py migrate_schemas --shared

# 3. Add to serializer (serializers.py)
class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = [..., "phone_number"]

# 4. Add to service (create_object parameters)
def create_object(self, ..., phone_number: str = "", **kwargs):
    # ...
    tenant.phone_number = phone_number
    tenant.save()
```

### Custom Management Command

```python
# tenants/management/commands/list_tenants.py
from django.core.management.base import BaseCommand
from tenants.models import Client

class Command(BaseCommand):
    help = 'Lists all tenants'
    
    def handle(self, *args, **options):
        tenants = Client.objects.exclude(schema_name='public')
        
        self.stdout.write(
            self.style.SUCCESS(f"Toplam {tenants.count()} tenant bulundu:")
        )
        
        for tenant in tenants:
            status = "Aktif" if tenant.is_active else "Pasif"
            self.stdout.write(
                f"  - {tenant.name} ({tenant.slug}): {status}"
            )

# Kullanım
uv run python manage.py list_tenants
```

### Tenant Migration

```bash
# Shared apps (public schema)
uv run python manage.py migrate_schemas --shared

# Tenant apps (tüm tenant schema'lar)
uv run python manage.py migrate_schemas

# Belirli bir tenant için
uv run python manage.py migrate_schemas --schema=evilcorp

# Yeni tenant oluşturulduğunda
# provision_tenant() otomatik migrate yapar
```

## Security Considerations

### 1. Schema Isolation

```python
# Her tenant kendi schema'sında çalışır
# Cross-tenant query mümkün değil
with tenant_context(tenant_a):
    employees_a = Employee.objects.all()  # Sadece tenant_a'nın verileri

with tenant_context(tenant_b):
    employees_b = Employee.objects.all()  # Sadece tenant_b'nin verileri

# employees_a ve employees_b tamamen farklı schema'lardan
```

### 2. Owner Protection

```python
# Tenant owner değiştirilemez
def update_object(self, instance, **kwargs):
    _owner = kwargs.pop("owner", None)  # owner parametresini kaldır
    # ...
```

### 3. Domain Uniqueness

```python
# Her tenant'ın unique domain'i olmalı
# Domain model'de unique=True
class Domain(DomainMixin):
    # domain = models.CharField(max_length=253, unique=True)
    pass
```

### 4. Soft Delete Pattern

```python
# Schema is never dropped (auto_drop_schema=False)
# Only deactivated
# Important for data recovery
```

## Common Pitfalls

### ❌ WRONG: Querying tenant app in public schema

```python
employees = Employee.objects.all()  # DoesNotExist error
```

### ✅ CORRECT: Use tenant context

```python
with tenant_context(tenant):
    employees = Employee.objects.all()
```

### ❌ WRONG: Manually creating schema

```python
# Creating schema with manual SQL
cursor.execute("CREATE SCHEMA evilcorp")  # Migrations won't run
```

### ✅ CORRECT: Use provision_tenant

```python
tenant, domain = provision_tenant("Evil Corp", "evilcorp", owner)
```

### ❌ YANLIŞ: Normal migrate komutu

```bash
uv run python manage.py migrate  # Sadece default schema
```

### ✅ DOĞRU: migrate_schemas kullan

```bash
uv run python manage.py migrate_schemas  # Tüm tenant schema'lar
```

## Quick Commands

```bash
# Public tenant oluştur (ilk kurulum)
uv run python manage.py shell
>>> from tenant_users.tenants.utils import create_public_tenant
>>> create_public_tenant(domain_url="localhost", owner_email="admin@localhost.com")

# Tenant listele
uv run python manage.py shell
>>> from tenants.models import Client
>>> Client.objects.exclude(schema_name='public').values('name', 'slug', 'is_active')

# Shared migration
uv run python manage.py migrate_schemas --shared

# Tenant migration
uv run python manage.py migrate_schemas

# Belirli tenant migration
uv run python manage.py migrate_schemas --schema=evilcorp

# Tenant shell
uv run python manage.py tenant_command shell --schema=evilcorp
```

## Dependencies

Bu modül şu modüllere bağımlıdır:

- **django-tenants:** Multi-tenancy framework
- **tenant-users:** User-tenant relationship
- **users:** User modeli (owner)
- **employees:** Employee oluşturma (owner)
- **utils:** BaseModel, BaseService

Bu modülü kullanan modüller:

- **employees:** Tenant context için
- **titles:** Tenant context için
- **auth:** Login response'da tenant bilgisi

## Middleware Configuration

```python
# config/settings.py
MIDDLEWARE = [
    "tenants.middleware.CustomTenantMiddleware",  # İlk sırada
    "django.middleware.security.SecurityMiddleware",
    # ...
]

TENANT_MODEL = "tenants.Client"
TENANT_DOMAIN_MODEL = "tenants.Domain"

# Public schema URL config
PUBLIC_SCHEMA_URLCONF = "config.public_urls"  # /public/* routes
ROOT_URLCONF = "config.urls"  # Tenant routes
```

## API Schema

Otomatik API dokümantasyonu:

```bash
# Swagger UI
http://localhost:8000/api/schema/swagger-ui/#/tenants

# ReDoc
http://localhost:8000/api/schema/redoc/#tag/tenants
```

---

**Coverage Target:** 80%
**Last Updated:** 2025-10-26
