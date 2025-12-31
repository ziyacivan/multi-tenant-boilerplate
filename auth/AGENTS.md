# auth/ AGENTS.md

Authentication & Authorization Module

## Module Overview

This module handles user authentication, registration, email verification, and password reset operations.

**Core Features:**
- JWT-based authentication (simplejwt)
- Email verification (6-digit code)
- Password reset (token-based)
- Async email sending with Celery
- Rate limiting (register endpoint)

**Dependencies:**
- `users` module (User model)
- `tenants` module (Client model)
- `utils` module (BaseService, exceptions)
- Celery + Redis (async tasks)

## Files Structure

```
auth/
├── __init__.py
├── exceptions.py          # Auth-specific exceptions
├── serializers.py         # DRF serializers
├── services.py            # Business logic (AuthService)
├── tasks.py               # Celery tasks (email sending)
├── urls.py                # URL routing
├── views.py               # API views
└── tests/
    ├── test_services.py   # Service layer tests
    └── test_views.py      # API endpoint tests
```

## Key Components

### 1. AuthService (`services.py`)

All authentication business logic lives here.

**Methods:**
- `validate_credentials(email, password)` - Credential validation for login
- `refresh_token(refresh_token)` - JWT token refresh
- `register(email, password)` - New user registration
- `verify_email(email, verification_code)` - Email verification
- `resend_verification_email(email)` - Resend verification code
- `request_password_reset(email, request)` - Password reset request
- `confirm_password_reset(uidb64, token, new_password)` - Password reset confirmation

**Important Variables:**
```python
VERIFICATION_CODE_LENGTH = 6
VERIFICATION_CODE_EXPIRY_MINUTES = 15
```

### 2. API Endpoints (`views.py`)

All endpoints use `AllowAny` permission.

```python
POST /auth/login/              # Login
POST /auth/refresh/            # Refresh token
POST /auth/register/           # Register (rate limited: 5/hour)
POST /auth/verify-email/       # Verify email
POST /auth/resend-verification/ # Resend verification code
POST /auth/password-reset/     # Password reset request
POST /auth/password-reset-confirm/ # Password reset confirmation
```

### 3. Celery Tasks (`tasks.py`)

Async email sending.

```python
@shared_task
def send_verification_email_task(email, verification_code, expires_at)
    # Sends email verification code

@shared_task
def send_reset_email_task(user_id, reset_url)
    # Sends password reset link
```

### 4. Custom Exceptions (`exceptions.py`)

```python
InvalidCredentialsException          # Invalid email/password
InvalidTokenException                # Invalid JWT token
InvalidVerificationCodeException     # Wrong verification code
UserAlreadyExistsException          # User already registered
UserNotActiveException              # User not active
UserNotVerifiedException            # Email not verified
UserAlreadyVerifiedException        # User already verified
UserIsAlreadyInVerificationProcessException  # Verification process in progress
```

## Common Patterns

### 1. User Registration Flow

```python
# Service layer
def register(self, email: str, password: str) -> bool:
    # 1. Check if user exists
    existing_user = User.objects.filter(email=email).first()
    if existing_user:
        if not existing_user.is_verified:
            raise UserIsAlreadyInVerificationProcessException()
        raise UserAlreadyExistsException()
    
    # 2. Generate verification code
    raw_verification_code = self._generate_verification_code()
    
    # 3. Create user (inactive)
    user = User.objects.create_user(
        email=email,
        password=password,
        is_active=False,
        verification_code_expires_at=timezone.now() + timedelta(minutes=15)
    )
    user.set_verification_code(raw_verification_code)
    user.save()
    
    # 4. Send async email
    send_verification_email_task.delay(email, raw_verification_code, ...)
    return True
```

### 2. Email Verification Flow

```python
@transaction.atomic
def verify_email(self, email: str, verification_code: str):
    user = User.objects.get(email=email)
    
    # 1. Check if code is valid
    if not self._is_valid_verification_code(user, verification_code):
        raise InvalidVerificationCodeException()
    
    # 2. Activate user
    user.is_verified = True
    user.is_active = True
    user.verification_code_verified_at = timezone.now()
    user.verification_code = ""
    user.verification_code_expires_at = None
    user.save()
    
    return {"email": email, "is_verified": True}
```

### 3. Password Reset Flow

```python
# Step 1: Request reset
def request_password_reset(self, email: str, request: Request):
    user = User.objects.get(email__iexact=email)
    
    # Create UID and token
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = self.token_generator.make_token(user)
    
    # Build reset URL
    reset_url = f"{settings.FRONTEND_URL}/reset/{uid}/{token}"
    
    # Send async email
    send_reset_email_task.delay(user.id, reset_url)

# Step 2: Confirm reset
@transaction.atomic
def confirm_password_reset(self, uidb64: str, token: str, new_password: str):
    user = self._get_user_from_uidb64(uidb64)
    
    if user and self.token_generator.check_token(user, token):
        user.set_password(new_password)
        user.save()
        return True, "Password has been reset successfully."
    
    return False, "The reset link is invalid or has expired."
```

## Testing Guidelines

### Test Coverage Target: 85%

### Service Tests (`test_services.py`)

```python
from django.test import TestCase
from model_bakery import baker
from auth.services import AuthService

class AuthServiceTestCase(TestCase):
    def setUp(self):
        self.service = AuthService()
    
    def test_validate_credentials_success(self):
        """Valid credentials should return JWT tokens"""
        user = baker.make("users.User", is_active=True, is_verified=True)
        user.set_password("password123")
        user.save()
        
        tokens, tenant = self.service.validate_credentials(
            user.email, "password123"
        )
        
        self.assertIn("access", tokens)
        self.assertIn("refresh", tokens)
    
    def test_validate_credentials_invalid_password(self):
        """Invalid password should raise exception"""
        user = baker.make("users.User", is_active=True, is_verified=True)
        user.set_password("password123")
        user.save()
        
        with self.assertRaises(InvalidCredentialsException):
            self.service.validate_credentials(user.email, "wrong_password")
```

### View Tests (`test_views.py`)

```python
from django.test import TestCase
from rest_framework.test import APIClient
from model_bakery import baker

class LoginViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/auth/login/"
    
    def test_login_success(self):
        """Valid login should return 200 with tokens"""
        user = baker.make("users.User", is_active=True, is_verified=True)
        user.set_password("password123")
        user.save()
        
        response = self.client.post(self.url, {
            "email": user.email,
            "password": "password123"
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
```

## Common Tasks

### Adding a New Authentication Endpoint

```python
# 1. Create serializer (serializers.py)
class NewAuthSerializer(serializers.Serializer):
    email = serializers.EmailField()
    # ... other fields

# 2. Add service method (services.py)
class AuthService:
    def new_auth_method(self, email: str, **kwargs):
        """
        New authentication method.
        
        Args:
            email (str): User email address
            **kwargs: Additional parameters
        
        Returns:
            dict: Operation result
        
        Raises:
            InvalidCredentialsException: Invalid credentials
        """
        # Business logic
        pass

# 3. Create view (views.py)
class NewAuthView(views.APIView):
    serializer_class = NewAuthSerializer
    permission_classes = [AllowAny]
    service_class = AuthService()
    
    @extend_schema(
        responses={200: {"type": "object"}},
        request=NewAuthSerializer
    )
    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = self.service_class.new_auth_method(**serializer.validated_data)
        return Response(result, status=status.HTTP_200_OK)

# 4. Add URL (urls.py)
urlpatterns = [
    # ...
    path("new-auth/", NewAuthView.as_view(), name="new-auth"),
]

# 5. Write test (tests/test_views.py)
def test_new_auth_success(self):
    response = self.client.post("/auth/new-auth/", {...})
    self.assertEqual(response.status_code, 200)
```

### Adding a New Celery Task

```python
# tasks.py
from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_custom_email_task(user_id: int, custom_data: str):
    """
    Sends custom email to user.
    
    Args:
        user_id (int): User ID
        custom_data (str): Custom data
    
    Returns:
        bool: True if successful
    """
    from users.models import User
    
    user = User.objects.get(pk=user_id)
    
    send_mail(
        subject="Custom Subject",
        message=f"Custom message: {custom_data}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
    return True

# Use in service
class AuthService:
    def some_method(self, user_id: int):
        # Sync operations
        # ...
        
        # Send async email
        send_custom_email_task.delay(user_id, "data")
```

## Security Considerations

### 1. Rate Limiting

```python
# RegisterView'da rate limiting aktif
class RegisterView(views.APIView):
    throttle_scope = "auth-register"  # 5/hour (settings.py)
```

### 2. Token Security

```python
# JWT token settings (settings.py)
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(hours=24),
    "ROTATE_REFRESH_TOKENS": True,  # New token on each refresh
    "BLACKLIST_AFTER_ROTATION": True,  # Blacklist old token
}
```

### 3. Password Hashing

```python
# User model uses bcrypt
user.set_password("raw_password")  # Automatically hashed
user.check_password("raw_password")  # Hash comparison
```

### 4. Verification Code Hashing

```python
# Verification code is stored hashed
raw_code = "ABC123"
user.set_verification_code(raw_code)  # Stored as hash
user.check_verification_code(raw_code)  # Hash comparison
```

## Error Handling

### Exception Response Format

```python
# Custom exception handler (utils/exceptions.py)
{
    "detail": "Error message",
    "code": "error_code"
}

# Example responses
InvalidCredentialsException -> 401 {"detail": "Invalid credentials"}
UserNotVerifiedException -> 403 {"detail": "Email not verified"}
InvalidTokenException -> 401 {"detail": "Invalid or expired token"}
```

## Quick Commands

```bash
# Run tests
uv run python manage.py test auth

# Test with coverage
uv run coverage run --source=auth manage.py test auth
uv run coverage report -m

# Specific test
uv run python manage.py test auth.tests.test_services.AuthServiceTestCase.test_register_success

# Start Celery worker (local development)
uv run celery -A config worker -l info

# Test in Django shell
uv run python manage.py shell
>>> from auth.services import AuthService
>>> service = AuthService()
>>> service.register("test@example.com", "password123")
```

## Common Pitfalls

### ❌ WRONG: Directly importing User model

```python
from users.models import User  # Circular import risk
```

### ✅ CORRECT: Use get_user_model

```python
from django.contrib.auth import get_user_model
User = get_user_model()
```

### ❌ WRONG: Synchronous email sending

```python
def register(self, email, password):
    # ...
    send_mail(...)  # Blocking operation
```

### ✅ CORRECT: Async Celery task

```python
def register(self, email, password):
    # ...
    send_verification_email_task.delay(...)  # Non-blocking
```

### ❌ WRONG: Plain text verification code

```python
user.verification_code = "ABC123"  # Plain text
```

### ✅ CORRECT: Hashed verification code

```python
user.set_verification_code("ABC123")  # Stored as hash
```

## Dependencies

This module depends on:

- **users:** User model and user management
- **tenants:** Client model (tenant information in login response)
- **utils:** BaseService, custom exceptions, EmailService

Modules that use this module:

- **employees:** User authentication required for employee records
- **tenants:** Owner authentication required for tenant creation

## API Schema

Automatic API documentation:

```bash
# Swagger UI
http://localhost:8000/api/schema/swagger-ui/#/auth

# ReDoc
http://localhost:8000/api/schema/redoc/#tag/auth
```

---

**Coverage Target:** 85%
**Last Updated:** 2025-10-26
