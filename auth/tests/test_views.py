from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone

from django_tenants.test.cases import TenantTestCase
from django_tenants.test.client import TenantClient
from model_bakery import baker
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User
from utils.tests.mixins import TenantTestCaseMixin


class LoginViewTestCase(TenantTestCaseMixin, TenantTestCase):
    """
    run: python manage.py test --keepdb auth.tests.test_views.LoginViewTestCase
    """

    @classmethod
    def get_test_tenant_domain(cls):
        return "test.localhost"

    @classmethod
    def get_test_schema_name(cls):
        return "test"

    def setUp(self):
        super().setUp()
        self.client = TenantClient(self.tenant)
        self.url = reverse("login")

        self.user = baker.make(User, email="test@example.com")
        self.user.set_password("password123")
        self.user.is_active = True
        self.user.is_verified = True
        self.user.save()

    def test_login_success(self):
        data = {
            "email": "test@example.com",
            "password": "password123",
        }
        response = self.client.post(self.url, data, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("refresh", response.data)
        self.assertIn("access", response.data)
        self.assertIsNotNone(response.data["refresh"])
        self.assertIsNotNone(response.data["access"])

    def test_login_invalid_credentials(self):
        data = {
            "email": "test@example.com",
            "password": "wrongpassword",
        }
        response = self.client.post(self.url, data, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_user_not_verified(self):
        self.user.is_verified = False
        self.user.save()

        data = {
            "email": "test@example.com",
            "password": "password123",
        }
        response = self.client.post(self.url, data, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_user_not_active(self):
        self.user.is_active = False
        self.user.save()

        data = {
            "email": "test@example.com",
            "password": "password123",
        }
        response = self.client.post(self.url, data, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_user_does_not_exist(self):
        data = {
            "email": "nonexistent@example.com",
            "password": "password123",
        }
        response = self.client.post(self.url, data, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_missing_email(self):
        data = {
            "password": "password123",
        }
        response = self.client.post(self.url, data, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_missing_password(self):
        data = {
            "email": "test@example.com",
        }
        response = self.client.post(self.url, data, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_invalid_email_format(self):
        data = {
            "email": "invalid-email",
            "password": "password123",
        }
        response = self.client.post(self.url, data, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RefreshTokenViewTestCase(TenantTestCaseMixin, TenantTestCase):
    """
    run: python manage.py test --keepdb auth.tests.test_views.RefreshTokenViewTestCase
    """

    @classmethod
    def get_test_tenant_domain(cls):
        return "test.localhost"

    @classmethod
    def get_test_schema_name(cls):
        return "test"

    def setUp(self):
        super().setUp()
        self.client = TenantClient(self.tenant)
        self.url = reverse("token-refresh")

        self.user = baker.make(User, email="test@example.com")
        self.user.set_password("password123")
        self.user.is_active = True
        self.user.is_verified = True
        self.user.save()

        self.refresh_token = RefreshToken.for_user(self.user)

    def test_refresh_token_success(self):
        data = {
            "refresh": str(self.refresh_token),
        }
        response = self.client.post(self.url, data, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("refresh", response.data)
        self.assertIn("access", response.data)
        self.assertIsNotNone(response.data["refresh"])
        self.assertIsNotNone(response.data["access"])

    def test_refresh_token_invalid(self):
        data = {
            "refresh": "invalid_token_string",
        }
        response = self.client.post(self.url, data, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_refresh_token_missing(self):
        data = {}
        response = self.client.post(self.url, data, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RegisterViewTestCase(TenantTestCaseMixin, TenantTestCase):
    """
    run: python manage.py test --keepdb auth.tests.test_views.RegisterViewTestCase
    """

    @classmethod
    def get_test_tenant_domain(cls):
        return "register-test.localhost"

    @classmethod
    def get_test_schema_name(cls):
        return "register_test"

    def setUp(self):
        super().setUp()
        self.client = TenantClient(self.tenant)
        self.url = reverse("register")

    @patch("auth.services.AuthService.register")
    def test_register_success(self, mock_register):
        mock_register.return_value = True

        data = {
            "email": "newuser@example.com",
            "password": "password123",
        }
        response = self.client.post(self.url, data, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_register.assert_called_once_with(
            email="newuser@example.com", password="password123"
        )

    def test_register_user_already_exists(self):
        user = baker.make(User, email="existing@example.com")
        user.set_password("password123")
        user.is_verified = True
        user.save()

        data = {
            "email": "existing@example.com",
            "password": "password123",
        }
        response = self.client.post(self.url, data, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_user_in_verification_process(self):
        user = baker.make(User, email="pending@example.com")
        user.set_password("password123")
        user.is_verified = False
        user.verification_code = "123456"
        user.verification_code_expires_at = timezone.now() + timezone.timedelta(
            minutes=15
        )
        user.save()

        data = {
            "email": "pending@example.com",
            "password": "password123",
        }
        response = self.client.post(self.url, data, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_register_missing_email(self):
        data = {
            "password": "password123",
        }
        response = self.client.post(self.url, data, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_password(self):
        data = {
            "email": "newuser@example.com",
        }
        response = self.client.post(self.url, data, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_invalid_email_format(self):
        data = {
            "email": "invalid-email",
            "password": "password123",
        }
        response = self.client.post(self.url, data, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class VerifyEmailViewTestCase(TenantTestCaseMixin, TenantTestCase):
    """
    run: python manage.py test --keepdb auth.tests.test_views.VerifyEmailViewTestCase
    """

    @classmethod
    def get_test_tenant_domain(cls):
        return "test.localhost"

    @classmethod
    def get_test_schema_name(cls):
        return "test"

    def setUp(self):
        super().setUp()
        self.client = TenantClient(self.tenant)
        self.url = reverse("verify-email")

        self.user = baker.make(User, email="test@example.com")
        self.user.set_password("password123")
        self.user.is_verified = False
        self.user.is_active = False
        self.user.verification_code = "ABC123"
        self.user.verification_code_expires_at = timezone.now() + timezone.timedelta(
            minutes=15
        )
        self.user.save()

    def test_verify_email_success(self):
        data = {
            "email": "test@example.com",
            "verification_code": "ABC123",
        }
        response = self.client.post(self.url, data, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("email", response.data)
        self.assertIn("is_verified", response.data)
        self.assertEqual(response.data["email"], "test@example.com")
        self.assertTrue(response.data["is_verified"])

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_verified)
        self.assertTrue(self.user.is_active)

    def test_verify_email_invalid_code(self):
        data = {
            "email": "test@example.com",
            "verification_code": "WRONG1",
        }
        response = self.client.post(self.url, data, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_email_expired_code(self):
        self.user.verification_code_expires_at = timezone.now() - timezone.timedelta(
            minutes=1
        )
        self.user.save()

        data = {
            "email": "test@example.com",
            "verification_code": "ABC123",
        }
        response = self.client.post(self.url, data, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_email_already_verified(self):
        self.user.is_verified = True
        self.user.save()

        data = {
            "email": "test@example.com",
            "verification_code": "ABC123",
        }
        response = self.client.post(self.url, data, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_email_user_not_found(self):
        data = {
            "email": "nonexistent@example.com",
            "verification_code": "ABC123",
        }
        response = self.client.post(self.url, data, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_verify_email_missing_email(self):
        data = {
            "verification_code": "ABC123",
        }
        response = self.client.post(self.url, data, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_email_missing_code(self):
        data = {
            "email": "test@example.com",
        }
        response = self.client.post(self.url, data, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_email_invalid_email_format(self):
        data = {
            "email": "invalid-email",
            "verification_code": "ABC123",
        }
        response = self.client.post(self.url, data, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ResendVerificationEmailViewTestCase(TenantTestCaseMixin, TenantTestCase):
    """
    run: python manage.py test --keepdb auth.tests.test_views.ResendVerificationEmailViewTestCase
    """

    @classmethod
    def get_test_tenant_domain(cls):
        return "test.localhost"

    @classmethod
    def get_test_schema_name(cls):
        return "test"

    def setUp(self):
        super().setUp()
        self.client = TenantClient(self.tenant)
        self.url = reverse("resend-verification-email")

        self.user = baker.make(User, email="test@example.com")
        self.user.set_password("password123")
        self.user.is_verified = False
        self.user.is_active = False
        self.user.verification_code = "ABC123"
        # Set expired verification code so resend is allowed
        self.user.verification_code_expires_at = timezone.now() - timezone.timedelta(
            minutes=1
        )
        self.user.save()

    @patch("auth.services.AuthService.resend_verification_email")
    def test_resend_verification_email_success(self, mock_resend):
        mock_resend.return_value = True

        data = {
            "email": "test@example.com",
        }
        response = self.client.post(self.url, data, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_resend.assert_called_once_with(email="test@example.com")

    def test_resend_verification_email_user_not_found(self):
        data = {
            "email": "nonexistent@example.com",
        }
        response = self.client.post(self.url, data, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_resend_verification_email_already_verified(self):
        self.user.is_verified = True
        self.user.save()

        data = {
            "email": "test@example.com",
        }
        response = self.client.post(self.url, data, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_resend_verification_email_still_valid(self):
        self.user.verification_code_expires_at = timezone.now() + timezone.timedelta(
            minutes=10
        )
        self.user.save()

        data = {
            "email": "test@example.com",
        }
        response = self.client.post(self.url, data, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_resend_verification_email_missing_email(self):
        data = {}
        response = self.client.post(self.url, data, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_resend_verification_email_invalid_email_format(self):
        data = {
            "email": "invalid-email",
        }
        response = self.client.post(self.url, data, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
