# utils/ AGENTS.md

Utility Module - Shared Components

## Module Overview

This module contains shared components (base classes, interfaces, mixins, exceptions) used throughout the project. Every module uses these utilities.

**Core Features:**
- BaseModel (abstract model)
- BaseService (service interface)
- Custom exception handler
- Test mixins (TenantTestCaseMixin, AuthenticatedTenantTestMixin)
- EmailService

**Dependencies:**
- Django core
- DRF (Django REST Framework)
- django-tenants

## Files Structure

```
utils/
├── __init__.py
├── exceptions.py          # Custom exception handler & base exceptions
├── interfaces.py          # BaseService interface (ABC)
├── mixins.py              # Permission mixins
├── models.py              # BaseModel abstract model
├── services.py            # EmailService
└── tests/
    └── mixins.py          # Test mixins (TenantTestCaseMixin, etc.)
```

## Key Components

### 1. BaseModel (`models.py`)

Abstract base model that all models extend.

```python
from django.db import models
from django.utils.translation import gettext_lazy as _

class BaseModel(models.Model):
    created_on = models.DateTimeField(_("created on"), auto_now_add=True)
    updated_on = models.DateTimeField(_("updated on"), auto_now=True)
    attributes = models.JSONField(_("attributes"), default=dict, blank=True)
    
    class Meta:
        abstract = True  # Does not create a database table
```

**Features:**
- `created_on`: Automatic creation timestamp
- `updated_on`: Automatic update timestamp
- `attributes`: Flexible JSON field (for extra data)

**Usage:**
```python
from utils.models import BaseModel

class Employee(BaseModel):
    # created_on, updated_on, attributes automatically included
    first_name = models.CharField(_("first name"), max_length=255)
    last_name = models.CharField(_("last name"), max_length=255)
```

### 2. BaseService Interface (`interfaces.py`)

ABC (Abstract Base Class) that all service classes implement.

```python
from abc import ABC, abstractmethod

class BaseService(ABC):
    @abstractmethod
    def create_object(self, *args, **kwargs):
        """Creates a new object."""
        ...
    
    @abstractmethod
    def update_object(self, *args, **kwargs):
        """Updates an object."""
        ...
    
    @abstractmethod
    def delete_object(self, *args, **kwargs):
        """Deletes an object."""
        ...
```

**Features:**
- ✅ Service layer standardization
- ✅ Interface guarantee with ABC
- ✅ Consistent naming (create_object, update_object, delete_object)

**Usage:**
```python
from utils.interfaces import BaseService

class EmployeeService(BaseService):
    def create_object(self, user, first_name, last_name, **kwargs):
        return Employee.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            **kwargs
        )
    
    def update_object(self, instance, **kwargs):
        for attr, value in kwargs.items():
            setattr(instance, attr, value)
        instance.save(update_fields=kwargs.keys())
        return instance
    
    def delete_object(self, instance, force=False):
        if force:
            instance.delete()
        else:
            instance.is_active = False
            instance.save()
```

### 3. Custom Exception Handler (`exceptions.py`)

Custom exception handler and base exceptions for DRF.

```python
from rest_framework.views import exception_handler as drf_exception_handler

def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF.
    
    Standard DRF response format:
    {
        "detail": "Error message",
        "code": "error_code"
    }
    """
    response = drf_exception_handler(exc, context)
    
    # Custom exception handling logic
    if response is not None:
        # Add custom fields
        response.data["status_code"] = response.status_code
    
    return response

class BaseAPIException(Exception):
    """Base exception for all API exceptions."""
    default_detail = "An error occurred."
    default_code = "error"
    status_code = 400
    
    def __init__(self, detail=None, code=None):
        self.detail = detail or self.default_detail
        self.code = code or self.default_code
```

**Usage:**
```python
# Define custom exception
class EmployeeNotFoundException(BaseAPIException):
    default_detail = "Employee not found."
    default_code = "employee_not_found"
    status_code = 404

# Raise exception
raise EmployeeNotFoundException()

# Response:
# {
#     "detail": "Employee not found.",
#     "code": "employee_not_found",
#     "status_code": 404
# }
```

### 4. EmailService (`services.py`)

Utility service for sending emails.

```python
from django.core.mail import send_mail
from django.conf import settings

class EmailService:
    @staticmethod
    def send_email(
        subject: str,
        message: str,
        recipient_list: list[str],
        from_email: str = None,
        html_message: str = None
    ):
        """
        Sends email.
        
        Args:
            subject (str): Email subject
            message (str): Plain text message
            recipient_list (list[str]): Recipient email addresses
            from_email (str, optional): Sender address
            html_message (str, optional): HTML message
        
        Returns:
            int: Number of emails sent
        """
        from_email = from_email or settings.DEFAULT_FROM_EMAIL
        
        return send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False
        )
```

### 5. Test Mixins (`tests/mixins.py`)

Mixins for tenant-aware testing.

**TenantTestCaseMixin:**
```python
class TenantTestCaseMixin:
    """
    Base mixin for tenant test setup.
    
    Features:
    - Create public tenant
    - Test tenant cleanup (for --keepdb)
    - Tenant setup
    """
    
    @classmethod
    def setUpClass(cls):
        cls._ensure_public_tenant_exists()
        cls._cleanup_existing_test_tenant()
        super().setUpClass()
    
    @classmethod
    def _ensure_public_tenant_exists(cls):
        """Creates public tenant if it doesn't exist."""
        # ...
    
    @classmethod
    def _cleanup_existing_test_tenant(cls):
        """Cleans up previous test tenant."""
        # ...
    
    @classmethod
    def setup_tenant(cls, tenant):
        """Configures test tenant."""
        # ...
```

**AuthenticatedTenantTestMixin:**
```python
class AuthenticatedTenantTestMixin(TenantTestCaseMixin):
    """
    Mixin for tenant tests requiring authentication.
    
    Features:
    - JWT token generation
    - Authenticated client setup
    - Helper methods (get, post, put, patch, delete)
    - Test user/employee creation
    """
    
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self._auth_token = None
        self.test_employee = None
    
    def authenticate_client(self, role=EmployeeRole.employee):
        """Authenticates client and sets token."""
        user = self.create_test_user(email=f"test_{role}@test.com")
        self.test_employee = self.create_test_employee(user=user, role=role)
        
        refresh = RefreshToken.for_user(user)
        self._auth_token = str(refresh.access_token)
        
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self._auth_token}")
    
    def create_test_user(self, email, **kwargs):
        """Creates test user."""
        # ...
    
    def create_test_employee(self, user=None, role=EmployeeRole.employee, **kwargs):
        """Creates test employee."""
        # ...
    
    def get(self, path, **kwargs):
        """Sends GET request (tenant header automatic)."""
        kwargs.setdefault("HTTP_X_CLIENT", self.tenant_id)
        return self.client.get(path, **kwargs)
    
    # post, put, patch, delete methods similar
```

## Common Patterns

### 1. Using BaseModel

```python
# ✅ CORRECT: Extend from BaseModel
from utils.models import BaseModel

class MyModel(BaseModel):
    name = models.CharField(max_length=255)
    
    class Meta:
        verbose_name = _("my model")
        verbose_name_plural = _("my models")

# Automatic fields:
# - created_on (auto_now_add=True)
# - updated_on (auto_now=True)
# - attributes (JSONField, default=dict)

# Usage
obj = MyModel.objects.create(name="Test")
print(obj.created_on)  # 2025-10-26 12:00:00
print(obj.updated_on)  # 2025-10-26 12:00:00
print(obj.attributes)  # {}

obj.attributes = {"key": "value"}
obj.save()
```

### 2. BaseService Implementation

```python
# ✅ CORRECT: Implement BaseService
from utils.interfaces import BaseService

class MyService(BaseService):
    def create_object(self, name, **kwargs):
        """Creates new object."""
        return MyModel.objects.create(name=name, **kwargs)
    
    def update_object(self, instance, **kwargs):
        """Updates object."""
        for attr, value in kwargs.items():
            setattr(instance, attr, value)
        instance.save(update_fields=kwargs.keys())
        return instance
    
    def delete_object(self, instance, force=False):
        """Deletes object."""
        if force:
            instance.delete()
        else:
            instance.is_active = False
            instance.save()

# Usage in view
class MyViewSet(viewsets.ModelViewSet):
    service_class = MyService()
    
    def perform_create(self, serializer):
        serializer.instance = self.service_class.create_object(
            **serializer.validated_data
        )
```

### 3. Defining Custom Exception

```python
# exceptions.py (each module has its own exceptions.py)
from utils.exceptions import BaseAPIException

class EmployeeNotFoundException(BaseAPIException):
    default_detail = "Employee not found."
    default_code = "employee_not_found"
    status_code = 404

class CannotDeleteEmployeeException(BaseAPIException):
    default_detail = "Cannot delete this employee."
    default_code = "cannot_delete_employee"
    status_code = 400

# Usage in service
def get_employee(employee_id):
    try:
        return Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        raise EmployeeNotFoundException()

def delete_employee(employee):
    if employee.role == EmployeeRole.owner:
        raise CannotDeleteEmployeeException()
    employee.delete()
```

### 4. Using TenantTestCaseMixin

```python
# For service tests
from django_tenants.test.cases import TenantTestCase
from utils.tests.mixins import TenantTestCaseMixin

class MyServiceTestCase(TenantTestCaseMixin, TenantTestCase):
    def setUp(self):
        super().setUp()
        self.service = MyService()
    
    def test_create_object(self):
        obj = self.service.create_object(name="Test")
        self.assertIsNotNone(obj)
        self.assertEqual(obj.name, "Test")

# For view tests (authentication required)
from utils.tests.mixins import AuthenticatedTenantTestMixin

class MyViewSetTestCase(AuthenticatedTenantTestMixin, TenantTestCase):
    def setUp(self):
        super().setUp()
        self.authenticate_client(role=EmployeeRole.manager)
    
    def test_list_success(self):
        response = self.get("/api/my-endpoint/")
        self.assertEqual(response.status_code, 200)
```

### 5. Using EmailService

```python
from utils.services import EmailService

# Simple email
email_service = EmailService()
email_service.send_email(
    subject="Welcome",
    message="Welcome to our platform!",
    recipient_list=["user@example.com"]
)

# HTML email
html_content = "<h1>Welcome</h1><p>Welcome to our platform!</p>"
email_service.send_email(
    subject="Welcome",
    message="Welcome to our platform!",  # Plain text fallback
    recipient_list=["user@example.com"],
    html_message=html_content
)
```

## Testing Guidelines

### Test Coverage Target: 90%

**High coverage reason:** Core utilities, used throughout the project.

### BaseModel Tests

```python
from django.test import TestCase
from utils.models import BaseModel

class ConcreteModel(BaseModel):
    name = models.CharField(max_length=255)
    
    class Meta:
        app_label = "utils"

class BaseModelTestCase(TestCase):
    def test_created_on_auto_set(self):
        """created_on should be set automatically"""
        obj = ConcreteModel.objects.create(name="Test")
        self.assertIsNotNone(obj.created_on)
    
    def test_updated_on_auto_update(self):
        """updated_on should update on save"""
        obj = ConcreteModel.objects.create(name="Test")
        old_updated_on = obj.updated_on
        
        time.sleep(0.1)
        obj.name = "Updated"
        obj.save()
        
        self.assertGreater(obj.updated_on, old_updated_on)
    
    def test_attributes_default_dict(self):
        """attributes should default to empty dict"""
        obj = ConcreteModel.objects.create(name="Test")
        self.assertEqual(obj.attributes, {})
```

### BaseService Tests

```python
class BaseServiceTestCase(TestCase):
    def test_abstract_methods_must_be_implemented(self):
        """BaseService cannot be instantiated directly"""
        with self.assertRaises(TypeError):
            BaseService()
    
    def test_service_implements_all_methods(self):
        """Service must implement all abstract methods"""
        class IncompleteService(BaseService):
            def create_object(self):
                pass
            # Missing update_object, delete_object
        
        with self.assertRaises(TypeError):
            IncompleteService()
```

### EmailService Tests

```python
from django.test import TestCase
from django.core import mail
from utils.services import EmailService

class EmailServiceTestCase(TestCase):
    def setUp(self):
        self.email_service = EmailService()
    
    def test_send_email_success(self):
        """Should send email successfully"""
        result = self.email_service.send_email(
            subject="Test Subject",
            message="Test Message",
            recipient_list=["test@example.com"]
        )
        
        self.assertEqual(result, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Test Subject")
```

## Common Tasks

### Yeni Bir BaseException Eklemek

```python
# utils/exceptions.py
class ResourceLockedException(BaseAPIException):
    """
    Kaynak kilitli olduğunda fırlatılır.
    """
    default_detail = "Resource is locked."
    default_code = "resource_locked"
    status_code = 423  # HTTP 423 Locked

# Kullanım
def update_resource(resource):
    if resource.is_locked:
        raise ResourceLockedException()
    # Update logic
```

### Yeni Bir Test Mixin Eklemek

```python
# utils/tests/mixins.py
class AdminTenantTestMixin(AuthenticatedTenantTestMixin):
    """
    Admin testleri için mixin.
    Otomatik olarak admin user ile authenticate eder.
    """
    
    def setUp(self):
        super().setUp()
        self.authenticate_as_admin()
    
    def authenticate_as_admin(self):
        """Admin user ile authenticate eder."""
        user = self.create_test_user(
            email="admin@test.com",
            is_staff=True,
            is_superuser=True
        )
        
        refresh = RefreshToken.for_user(user)
        self._auth_token = str(refresh.access_token)
        
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self._auth_token}")

# Kullanım
class AdminViewTestCase(AdminTenantTestMixin, TenantTestCase):
    def test_admin_action(self):
        # Otomatik admin authentication
        response = self.get("/api/admin-endpoint/")
        self.assertEqual(response.status_code, 200)
```

### BaseModel'e Ortak Field Eklemek

```python
# utils/models.py
class BaseModel(models.Model):
    created_on = models.DateTimeField(_("created on"), auto_now_add=True)
    updated_on = models.DateTimeField(_("updated on"), auto_now=True)
    attributes = models.JSONField(_("attributes"), default=dict, blank=True)
    
    # Yeni ortak field
    is_deleted = models.BooleanField(
        _("is deleted"),
        default=False,
        db_index=True,
        help_text=_("Soft delete flag")
    )
    
    class Meta:
        abstract = True
    
    def soft_delete(self):
        """Soft delete işlemi yapar."""
        self.is_deleted = True
        self.save(update_fields=["is_deleted"])
    
    def restore(self):
        """Soft delete'i geri alır."""
        self.is_deleted = False
        self.save(update_fields=["is_deleted"])

# Tüm modeller otomatik olarak bu field'ı alır
```

## Security Considerations

### 1. Exception Detail Exposure

```python
# ❌ YANLIŞ: Sensitive data expose etme
class InvalidPasswordException(BaseAPIException):
    def __init__(self, attempted_password):
        self.detail = f"Invalid password: {attempted_password}"  # Güvenlik riski

# ✅ DOĞRU: Generic message
class InvalidPasswordException(BaseAPIException):
    default_detail = "Invalid credentials."
    default_code = "invalid_credentials"
```

### 2. BaseModel attributes Field

```python
# ⚠️ Warning: attributes JSONField may allow open access
# Filter in serializer
class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        exclude = ["attributes"]  # Hide attributes from API
        # or
        fields = ["id", "name", ...]  # Don't include attributes
```

### 3. Custom Exception Handler

```python
# Don't show debug info in production
def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    
    if response is not None:
        # ❌ Don't show stack trace even in debug mode
        if settings.DEBUG:
            response.data["debug_info"] = str(exc)  # Security risk
        
        # ✅ Only generic error message
        response.data["status_code"] = response.status_code
    
    return response
```

## Quick Commands

```bash
# Run utils tests
uv run python manage.py test utils

# Test with coverage
uv run coverage run --source=utils manage.py test utils
uv run coverage report -m

# Test in Django shell
uv run python manage.py shell
>>> from utils.models import BaseModel
>>> from utils.interfaces import BaseService
>>> from utils.services import EmailService
```

## Dependencies

This module depends on:

- **Django core:** models, exceptions
- **DRF:** exception_handler, APIException
- **django-tenants:** TenantTestCase, tenant_context

Modules that use this module:

- **auth:** BaseService, exceptions
- **employees:** BaseModel, BaseService, test mixins
- **tenants:** BaseModel, BaseService, test mixins
- **titles:** BaseModel, BaseService, test mixins
- **users:** BaseModel

**⚠️ Important:** utils module must not depend on any application (auth, employees, tenants, users). Circular import risk.

## Common Pitfalls

### ❌ WRONG: Importing app from utils

```python
# utils/services.py
from employees.models import Employee  # Circular import risk
```

### ✅ CORRECT: Importing utils from apps

```python
# employees/services.py
from utils.interfaces import BaseService  # ✅ Doğru yön
```

### ❌ WRONG: Using BaseModel directly

```python
# models.py
from utils.models import BaseModel

BaseModel.objects.create(name="Test")  # Error: abstract model
```

### ✅ CORRECT: Extending from BaseModel

```python
class MyModel(BaseModel):
    name = models.CharField(max_length=255)

MyModel.objects.create(name="Test")  # ✅
```

## Best Practices

1. **Always extend BaseModel:**
```python
class MyModel(BaseModel):  # ✅
    pass
```

2. **Always implement BaseService:**
```python
class MyService(BaseService):  # ✅
    def create_object(self, **kwargs): pass
    def update_object(self, instance, **kwargs): pass
    def delete_object(self, instance): pass
```

3. **Test mixins combination:**
```python
# Service tests
class MyServiceTest(TenantTestCaseMixin, TenantTestCase):
    pass

# View tests (authentication required)
class MyViewTest(AuthenticatedTenantTestMixin, TenantTestCase):
    pass
```

4. **Exception naming convention:**
```python
{Resource}{Action}Exception
# Examples:
EmployeeNotFoundException
CannotDeleteEmployeeException
UserAlreadyExistsException
```

---

**Coverage Target:** 90%
**Last Updated:** 2025-10-26
