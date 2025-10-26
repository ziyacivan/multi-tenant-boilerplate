# AGENTS.md

HRM API - Multi-tenant Human Resource Management System

## Project Overview

This project is a multi-tenant Human Resource Management System API built with Django 5.2.7 and django-tenants. Each tenant (company) operates in its own schema, and data is completely isolated.

**Core Technologies:**
- Django 5.2.7 + Django REST Framework
- django-tenants (multi-tenancy)
- PostgreSQL (tenant-per-schema)
- JWT Authentication (djangorestframework-simplejwt)
- Celery + Redis (async tasks)
- Docker + docker-compose
- Python 3.13

**Project Language Standards:**
- **Code & Docstrings:** English
- **Comments:** English
- **verbose_name:** English with Django translation (_("text"))
- **i18n Support:** Multi-language via Django's translation system

## Setup Commands

### Local Development (Docker)

```bash
# Clone the project and copy the environment file
cp .env.example .env

# Start docker containers
docker-compose up -d

# Run database migrations
docker-compose exec web uv run python manage.py migrate_schemas --shared
docker-compose exec web uv run python manage.py migrate_schemas

# Create public tenant (first-time setup)
docker-compose exec web uv run python manage.py shell
>>> from tenant_users.tenants.utils import create_public_tenant
>>> create_public_tenant(domain_url="localhost", owner_email="admin@localhost.com")
>>> exit()

# Development server starts automatically (port 8000)
```

### Local Development (Native)

```bash
# Install dependencies with uv
uv sync --extra dev

# Make sure PostgreSQL and Redis are running
# Configure .env file

# Run migrations
uv run python manage.py migrate_schemas --shared
uv run python manage.py migrate_schemas

# Start development server
uv run python manage.py runserver

# Start Celery worker (separate terminal)
uv run celery -A config worker -l info
```

### Testing

```bash
# Run all tests
uv run python manage.py test

# Run tests for specific module
uv run python manage.py test employees
uv run python manage.py test auth

# Run tests with coverage
uv run coverage run --source=employees manage.py test employees
uv run coverage report

# Generate HTML coverage report
uv run coverage html
# open htmlcov/index.html

# Parallel module tests like CI pipeline (manual on local)
uv run coverage run --source=auth manage.py test auth
uv run coverage run --source=employees manage.py test employees
uv run coverage run --source=titles manage.py test titles
```

### Code Formatting

```bash
# Format code (Black + isort run automatically)
uv run black .
uv run isort .

# Or use uv format (recommended)
uv format

# Check formatting (runs in CI)
uv format --check
```

## Architecture Patterns

### 1. Multi-Tenant Architecture

**CRITICAL:** All tenant-aware operations must be performed within `tenant_context()`.

```python
from django_tenants.utils import tenant_context
from tenants.models import Client

tenant = Client.objects.get(schema_name="evilcorp")

with tenant_context(tenant):
    # All ORM queries within this block run in the tenant's schema
    employees = Employee.objects.all()
```

**Schema Types:**
- **Public Schema:** Shared apps (tenants, users)
- **Tenant Schema:** Each tenant has its own schema (employees, titles)

**Domain Routing:** CustomTenantMiddleware provides domain-based routing.

### 2. Service Layer Pattern

**All business logic should be in the Service layer.** Views only handle HTTP.

```python
# ✅ CORRECT: Service layer usage
from utils.interfaces import BaseService

class EmployeeService(BaseService):
    def create_object(self, user, first_name, last_name, **kwargs):
        """Creates a new employee."""
        employee = Employee.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            **kwargs
        )
        # Business logic here
        return employee

    def update_object(self, instance, **kwargs):
        """Updates employee information."""
        for attr, value in kwargs.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def delete_object(self, instance, force=False):
        """Deletes employee or performs soft delete."""
        if force:
            instance.delete()
        else:
            instance.is_active = False
            instance.save()
        return instance
```

```python
# Using service in view
class EmployeeViewSet(viewsets.ModelViewSet):
    service_class = EmployeeService()
    
    def perform_create(self, serializer):
        serializer.instance = self.service_class.create_object(
            **serializer.validated_data
        )
```

### 3. Model Standard

All models should extend `BaseModel` and use English verbose_name with Django translation.

```python
from django.db import models
from django.utils.translation import gettext_lazy as _
from utils.models import BaseModel

class Employee(BaseModel):  # BaseModel: created_on, updated_on, attributes
    user = models.OneToOneField(
        "users.User", 
        on_delete=models.CASCADE, 
        verbose_name=_("user")
    )
    first_name = models.CharField(_("first name"), max_length=255)
    last_name = models.CharField(_("last name"), max_length=255)
    role = models.CharField(
        _("role"),
        max_length=20,
        choices=EmployeeRole.choices,
        default=EmployeeRole.employee,
    )
    is_active = models.BooleanField(_("is active"), default=True)

    class Meta:
        verbose_name = _("employee")
        verbose_name_plural = _("employees")
        ordering = ["-created_on"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
```

### 4. Testing Pattern

Test classes should use `TenantTestCaseMixin`.

```python
from django_tenants.test.cases import TenantTestCase
from model_bakery import baker
from utils.tests.mixins import TenantTestCaseMixin, AuthenticatedTenantTestMixin

# Service tests
class EmployeeServiceTestCase(TenantTestCaseMixin, TenantTestCase):
    def setUp(self):
        super().setUp()
        self.service = EmployeeService()

    def test_create_object_success(self):
        user = baker.make("users.User")
        employee = self.service.create_object(
            user=user,
            first_name="Jane",
            last_name="Doe",
        )
        self.assertIsNotNone(employee)
        self.assertEqual(employee.first_name, "Jane")

# View tests (authentication required)
class EmployeeViewSetTestCase(AuthenticatedTenantTestMixin, TenantTestCase):
    def setUp(self):
        super().setUp()
        self.authenticate_client(role=EmployeeRole.manager)

    def test_list_success(self):
        response = self.get("/api/employees/")
        self.assertEqual(response.status_code, 200)
```

## Code Style Guidelines

### Formatting Rules

- **Black:** line-length=88, target-version=py313
- **isort:** profile="black"
- **Type hints:** Use as much as possible (Python 3.13+ compatible)
- **Docstrings:** Google style, English
- **Line length:** Maximum 88 characters

### Naming Conventions

```python
# Classes: PascalCase
class EmployeeService:
    pass

# Functions and variables: snake_case
def create_employee(first_name, last_name):
    employee_data = {...}
    return employee_data

# Constants: UPPER_CASE
MAX_UPLOAD_SIZE = 5 * 1024 * 1024

# Private: _prefix
def _internal_helper():
    pass
```

### Import Order

```python
# 1. Standard library
import os
from datetime import datetime

# 2. Django
from django.db import models
from django.utils.translation import gettext_lazy as _

# 3. Third-party
from rest_framework import viewsets
from django_tenants.utils import tenant_context

# 4. First-party (local apps)
from auth.serializers import RegisterSerializer
from employees.models import Employee
from tenants.models import Client
from users.models import User
from utils.interfaces import BaseService

# 5. Local folder
from .models import Title
from .serializers import TitleSerializer
```

### Docstring Pattern

```python
def create_employee(user, first_name, last_name, role=EmployeeRole.employee):
    """
    Creates a new employee record.

    Args:
        user (User): User object
        first_name (str): Employee's first name
        last_name (str): Employee's last name
        role (EmployeeRole, optional): Employee's role. Default: employee

    Returns:
        Employee: Created employee object

    Raises:
        ValidationError: On invalid data input
        EmployeeAlreadyExistsException: If user is already an employee

    Example:
        >>> user = User.objects.get(email="john@example.com")
        >>> employee = create_employee(user, "John", "Doe", EmployeeRole.manager)
    """
    # Implementation
    pass
```

## Common Tasks

### Creating a New Model

```bash
# 1. Create model file (example: employees/models.py)
# 2. Extend from BaseModel and use English verbose_name with _()
# 3. Create migration
uv run python manage.py makemigrations employees

# 4. Apply migration (tenant-aware)
uv run python manage.py migrate_schemas
```

### Creating a New API Endpoint

```python
# 1. Create serializer (employees/serializers.py)
from rest_framework import serializers

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ["id", "first_name", "last_name", "role", "is_active"]

# 2. Create service (employees/services.py)
class EmployeeService(BaseService):
    def create_object(self, **kwargs):
        return Employee.objects.create(**kwargs)
    # ... other methods

# 3. Create ViewSet (employees/views.py)
from rest_framework import viewsets
from drf_spectacular.utils import extend_schema

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    service_class = EmployeeService()
    
    @extend_schema(
        summary="List employees",
        description="Returns all active employees for the tenant"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

# 4. Add URL (employees/urls.py or config/urls.py)
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'employees', EmployeeViewSet)
```

### Creating a New Test

```python
# employees/tests/test_services.py
from django_tenants.test.cases import TenantTestCase
from model_bakery import baker
from utils.tests.mixins import TenantTestCaseMixin
from employees.services import EmployeeService

class EmployeeServiceTestCase(TenantTestCaseMixin, TenantTestCase):
    def setUp(self):
        super().setUp()
        self.service = EmployeeService()

    def test_create_object_success(self):
        user = baker.make("users.User")
        employee = self.service.create_object(
            user=user,
            first_name="Test",
            last_name="User"
        )
        self.assertIsNotNone(employee)
        self.assertEqual(employee.user, user)

# Run test
uv run python manage.py test employees.tests.test_services
```

### Creating a Celery Task

```python
# auth/tasks.py
from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_verification_email(user_email, verification_link):
    """
    Sends verification email to user.
    
    Args:
        user_email (str): User email address
        verification_link (str): Verification link
    
    Returns:
        bool: True if successful
    """
    send_mail(
        subject="Email Verification",
        message=f"Verification link: {verification_link}",
        from_email="noreply@example.com",
        recipient_list=[user_email],
    )
    return True

# Usage
from auth.tasks import send_verification_email
send_verification_email.delay("user@example.com", "http://...")
```

### Tenant Operations

```python
# Create new tenant
from users.models import User
from tenant_users.tenants.tasks import provision_tenant

owner = User.objects.create_user(
    email="owner@company.com",
    password="secure_password",
    is_staff=True
)
tenant, domain = provision_tenant("Company Name", "company", owner)

# Add user to tenant
from tenants.models import Client
tenant = Client.objects.get(schema_name="company")
user = User.objects.get(email="employee@company.com")
tenant.add_user(user)

# Perform operation in tenant context
from django_tenants.utils import tenant_context

with tenant_context(tenant):
    employees = Employee.objects.filter(is_active=True)
    # All ORM queries run in this tenant's schema
```

## Testing Instructions

### Coverage Targets

Minimum coverage rates for each module:
- **auth:** 85%
- **employees:** 80%
- **tenants:** 80%
- **users:** 75%
- **utils:** 90%
- **titles:** 95%

### Test Commands

```bash
# Run a single test file
uv run python manage.py test employees.tests.test_services.EmployeeServiceTestCase

# Run a specific test method
uv run python manage.py test employees.tests.test_services.EmployeeServiceTestCase.test_create_object_success

# Run with coverage and get report
uv run coverage run --source=employees manage.py test employees
uv run coverage report -m

# Generate HTML coverage report (open in browser)
uv run coverage html
open htmlcov/index.html
```

### Testing Best Practices

1. **Each test should be isolated:** Use `setUp()` and `tearDown()`
2. **Use Model Bakery:** Avoid unnecessary fixtures
3. **Tenant context:** Use `TenantTestCaseMixin`
4. **Descriptive names:** Test names should be explanatory
5. **AAA Pattern:** Arrange, Act, Assert

```python
def test_delete_employee_soft_delete(self):
    # Arrange (Setup)
    employee = baker.make("employees.Employee", is_active=True)
    
    # Act (Action)
    self.service.delete_object(employee, force=False)
    
    # Assert (Verification)
    employee.refresh_from_db()
    self.assertFalse(employee.is_active)
```

## Security Considerations

### Authentication

- **JWT tokens:** Access token (60 min), Refresh token (24 hours)
- **Token rotation:** New token generated on each refresh
- **Password hashing:** bcrypt is used
- **Permission classes:** IsAuthenticated, IsMinimumManagerOrReadOnly

### Tenant Isolation

- **Schema separation:** Each tenant operates in its own schema
- **Middleware check:** CustomTenantMiddleware checks every request
- **Cross-tenant queries:** Never perform these, use `tenant_context()`

### Sensitive Data

```python
# ❌ WRONG: Hardcoded sensitive data
API_KEY = "sk-1234567890abcdef"

# ✅ CORRECT: Use environment variable
import os
API_KEY = os.getenv("API_KEY")
```

### Validation

```python
# Validation in serializer
class EmployeeSerializer(serializers.ModelSerializer):
    def validate_email(self, value):
        """Checks email format."""
        if not value or "@" not in value:
            raise serializers.ValidationError("Enter a valid email address")
        return value
```

## CI/CD Pipeline

### GitHub Actions Workflow

Pipeline runs in 3 stages:

1. **Formatting Check:** Code formatting check (parallel)
2. **Setup & Cache:** Create dependency cache (parallel)
3. **Module Tests:** Each module tested in parallel

```bash
# Steps running in CI
uv format --check                           # Format check
uv run coverage run --source=auth manage.py test auth
uv run coverage run --source=employees manage.py test employees
uv run coverage run --source=titles manage.py test titles
```

### Pre-commit Checklist

Pre-commit checklist:

```bash
# 1. Format code
uv format

# 2. Run tests
uv run python manage.py test

# 3. Coverage check
uv run coverage run manage.py test
uv run coverage report

# 4. Migration check
uv run python manage.py makemigrations --check --dry-run

# 5. Commit
git add .
git commit -m "feat: add new feature"
git push origin feature/branch-name
```

## Deployment

### Docker Production

```bash
# Production build
docker-compose -f docker-compose.prod.yml build

# Start containers
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose exec web uv run python manage.py migrate_schemas --shared
docker-compose exec web uv run python manage.py migrate_schemas

# Collect static files
docker-compose exec web uv run python manage.py collectstatic --noinput
```

### Environment Variables

Required variables in `.env` file:

```bash
SECRET_KEY=your-secret-key-here
DEBUG=False
DB_NAME=hrm_db
DB_USER=hrm_user
DB_PASSWORD=secure_password
DB_HOST=db
DB_PORT=5432
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
CORS_ALLOWED_ORIGINS=https://yourdomain.com
```

## Common Pitfalls & Solutions

### Problem: N+1 Query

```python
# ❌ WRONG: N+1 query problem
employees = Employee.objects.all()
for emp in employees:
    print(emp.user.email)  # New query on each iteration

# ✅ CORRECT: Use select_related
employees = Employee.objects.select_related('user').all()
for emp in employees:
    print(emp.user.email)  # Single query
```

### Problem: Tenant Context Error

```python
# ❌ WRONG: Accessing tenant record in public schema
employee = Employee.objects.get(id=1)  # DoesNotExist error

# ✅ CORRECT: Use tenant context
from django_tenants.utils import tenant_context
from tenants.models import Client

tenant = Client.objects.get(schema_name="company")
with tenant_context(tenant):
    employee = Employee.objects.get(id=1)
```

### Problem: Migration Order

```bash
# ❌ WRONG: Normal migrate
uv run python manage.py migrate

# ✅ CORRECT: Tenant-aware migrate
uv run python manage.py migrate_schemas --shared    # First shared apps
uv run python manage.py migrate_schemas              # Then tenant apps
```

### Problem: Circular Import

```python
# ❌ WRONG: Importing service in model
# models.py
from .services import EmployeeService  # Circular import

# ✅ CORRECT: Import in function or be careful with structure
# views.py
from .services import EmployeeService  # Import in view
```

## Debugging Tips

### Django Shell

```bash
# Enter Django shell
docker-compose exec web uv run python manage.py shell

# or locally
uv run python manage.py shell
```

```python
# Debug in tenant context
from django_tenants.utils import tenant_context
from tenants.models import Client
from employees.models import Employee

tenant = Client.objects.get(schema_name="company")
with tenant_context(tenant):
    employees = Employee.objects.all()
    print(f"Total employees: {employees.count()}")
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

def create_employee(**kwargs):
    logger.info(f"Creating new employee: {kwargs}")
    # ...
    logger.debug(f"Employee created: {employee.id}")
```

### Debug Toolbar (Development)

```bash
# Automatically active when DEBUG=True
# http://localhost:8000/__debug__/
```

## API Documentation

### OpenAPI Schema

API documentation is automatically generated (drf-spectacular):

```bash
# Swagger UI
http://localhost:8000/api/schema/swagger-ui/

# ReDoc
http://localhost:8000/api/schema/redoc/

# OpenAPI JSON
http://localhost:8000/api/schema/
```

### Endpoint Documentation

```python
from drf_spectacular.utils import extend_schema, OpenApiParameter

@extend_schema(
    summary="Create employee",
    description="Creates a new employee record",
    request=EmployeeSerializer,
    responses={201: EmployeeSerializer},
    parameters=[
        OpenApiParameter(
            name="role",
            description="Employee role (employee, manager, owner)",
            required=False,
            type=str
        )
    ]
)
def create(self, request, *args, **kwargs):
    return super().create(request, *args, **kwargs)
```

## Additional Resources

### Project Documentation

- **Setup:** `docs/setup.md` - Setup steps
- **Tenants:** `docs/tenantlar.md` - Multi-tenant architecture
- **Migrations:** `docs/migrationlar.md` - Migration strategies
- **Docker:** `docs/docker.md` - Docker deployment
- **CI Pipeline:** `docs/ci-pipeline.md` - CI/CD configuration
- **Create Company Flow:** `docs/flows/create_company.md` - Company creation flow

### External Links

- Django Tenants: https://django-tenants.readthedocs.io/
- Django REST Framework: https://www.django-rest-framework.org/
- Celery: https://docs.celeryq.dev/
- drf-spectacular: https://drf-spectacular.readthedocs.io/

## Agent Behavior Guidelines

As an AI agent, when generating code:

1. **Always use English documentation:** Docstrings, comments, and verbose_name in English
2. **Use Django's translation system:** verbose_name with _("text") for i18n support
3. **Be tenant-aware:** Don't forget multi-tenant context
4. **Use service layer:** Business logic in services, not views
5. **Write tests:** Add tests for every new function/class
6. **Add type hints:** Use Python 3.13+ type hints
7. **Black formatting:** Code formatting must follow Black standards
8. **Use BaseModel/BaseService:** Follow inheritance patterns
9. **Security first:** Sensitive data in .env, always validate

## Quick Reference

```bash
# Common commands
uv run python manage.py runserver              # Dev server
uv run python manage.py shell                  # Django shell
uv run python manage.py makemigrations         # Create migration
uv run python manage.py migrate_schemas        # Apply migration
uv run python manage.py test <app>             # Run tests
uv run coverage run manage.py test             # Test with coverage
uv format                                      # Format code
docker-compose up -d                           # Start Docker
docker-compose logs -f web                     # View logs
docker-compose exec web bash                   # Enter container
```

---

**Last Updated:** 2025-10-26
**Project Version:** 0.1.0
**Python Version:** 3.13
**Django Version:** 5.2.7
