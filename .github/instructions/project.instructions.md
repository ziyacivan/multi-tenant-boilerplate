---
applyTo: '**'
---
## Copilot Instructions
This file defines the rules and standards that GitHub Copilot should follow when generating code suggestions for this project (HRM API). Copilot should use these instructions to provide consistent, high-quality code suggestions that comply with project standards.

## General Rules
- **Language:** All code suggestions should include English comments and documentation (the project is developed with English language support).
- **Code Quality:** Suggested code should be readable, maintainable, and performant. Unnecessary complexity should be avoided.
- **Test-Driven Development:** Provide test suggestions for every new function or class. Follow existing test patterns (e.g., use of TenantTestCaseMixin).
- **Error Handling:** Suggest appropriate exception handling. Use project-specific exceptions (e.g., BaseAPIException subclasses).
- **Documentation:** Add docstrings for functions and classes. Use DRF's extend_schema decorator for API endpoints.
- **Security:** Suggest appropriate validation and encryption for sensitive data (passwords, tokens).
- **Performance:** Prevent N+1 problems in database queries. Use select_related and prefetch_related.

## Coding Standards
- **Formatting:** Follow Black standards (line-length: 88, target-version: py313). All suggestions should be in Black format.
- **Import Ordering:** According to isort (profile: black) rules:
    - Standard library
    - Django
    - Third-party
    - First-party (auth, config, employees, tenants, users, utils)
    - Local folder
- **Naming Conventions:**
    - Classes: PascalCase
    - Functions: snake_case
    - Variables: snake_case
    - Constants: UPPER_CASE
- **Line Length:** Do not exceed 88 characters.
- **Docstrings:** Use Google style docstrings.
- **Type Hints:** Add type hints whenever possible (Python 3.13+ compatible).

## Technology Stack and Architecture
- **Framework:** Django 5.2.7, DRF (djangorestframework), django-tenants (multi-tenant architecture).
- **Authentication:** JWT (djangorestframework-simplejwt).
- **Database:** PostgreSQL, multi-tenant schemas.
- **Asynchronous Tasks:** Celery + Redis.
- **Email:** Django email backend, SendGrid integration.
- **Testing:** Django test framework, model-bakery, coverage (module-based minimum percentages: auth:85, tenants:80, users:75, employees:80, titles:95, utils:90).
- **Deployment:** Docker, docker-compose.
- **CI/CD:** GitHub Actions (formatting check, parallel module tests, coverage control).

## Tenant-Aware Coding
- All models and queries should operate within tenant context. Use `tenant_context()`.
- Distinguish between public schema (shared apps) and tenant schemas (tenant apps).
- Prefer TenantUser model for user operations.
- Use CustomTenantMiddleware for domain routing.

## API Design
- Follow RESTful API principles.
- Use ModelSerializer for serializers.
- **Permissions:** IsAuthenticated, IsMinimumManagerOrReadOnly and other project-specific permissions.
- **Pagination:** PageNumberPagination (page_size: 20).
- Use drf-spectacular for schema documentation.

## Code Pattern Examples

### Model Example
```python
from django.db import models
from django.utils.translation import gettext_lazy as _

from utils.models import BaseModel


class Employee(BaseModel):
    user = models.OneToOneField(
        "users.User", on_delete=models.CASCADE, verbose_name=_("user")
    )
    first_name = models.CharField(_("first name"), max_length=255)
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

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
```

### View Example
```python
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from employees.models import Employee
from employees.serializers import EmployeeSerializer
from employees.services import EmployeeService


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all().order_by("-created_on")
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated]
    service_class = EmployeeService()

    def perform_create(self, serializer):
        serializer.instance = self.service_class.create_object(
            **serializer.validated_data
        )
```

### Test Example
```python
from django_tenants.test.cases import TenantTestCase
from model_bakery import baker

from employees.models import Employee
from utils.tests.mixins import TenantTestCaseMixin


class EmployeeServiceTestCase(TenantTestCaseMixin, TenantTestCase):
    def test_create_object_success(self):
        user = baker.make("users.User")
        employee = self.service.create_object(
            user=user,
            first_name="Jane",
            last_name="Doe",
        )
        self.assertIsNotNone(employee)
        self.assertEqual(employee.user, user)
```

### Service Example
```python
from utils.interfaces import BaseService


class EmployeeService(BaseService):
    def create_object(self, user, first_name, last_name, **kwargs):
        employee = Employee.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            **kwargs
        )
        return employee

    def update_object(self, instance, **kwargs):
        for attr, value in kwargs.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def delete_object(self, instance):
        instance.delete()
```

## Prohibited Practices and Things to Avoid
- **Hardcoded Values:** Get configuration values from .env or settings.
- **Global State:** Do not use global variables outside tenant context.
- **Raw SQL:** Use ORM whenever possible. If raw SQL is necessary, add explanation.
- **Magic Numbers/Strings:** Define them as constants.
- **Print Statements:** Use logging (Django logging).
- **Direct Database Access:** Perform operations through service layer.
- **Blocking Operations:** Use Celery for async tasks.
- **Security Vulnerabilities:** Prevent risks such as SQL injection, XSS, etc.
