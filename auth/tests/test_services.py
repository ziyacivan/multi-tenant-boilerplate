from unittest.mock import patch

from django.utils import timezone

from django_tenants.test.cases import TenantTestCase
from django_tenants.test.client import TenantClient
from model_bakery import baker
from rest_framework_simplejwt.tokens import RefreshToken

from auth.exceptions import (
    InvalidCredentialsException,
    InvalidTokenException,
    InvalidVerificationCodeException,
    UserAlreadyExistsException,
    UserAlreadyVerifiedException,
    UserIsAlreadyInVerificationProcessException,
    UserNotActiveException,
    UserNotVerifiedException,
)
from auth.services import AuthService
from users.models import User
from utils.tests.mixins import TenantTestCaseMixin


class AuthServiceTestCase(TenantTestCaseMixin, TenantTestCase):
    """
    run: python manage.py test --keepdb auth.tests.test_services.AuthServiceTestCase
    """

    service = AuthService()

    @classmethod
    def get_test_tenant_domain(cls):
        return "test.localhost"

    @classmethod
    def get_test_schema_name(cls):
        return "test"

    def setUp(self):
        self.user = baker.make(User)
        self.user.set_password("password")
        self.user.is_active = True
        self.user.is_verified = True
        self.user.save()

        self.refresh_token = RefreshToken.for_user(self.user)

        self.client = TenantClient(self.tenant)

    def test_validate_credentials_success(self):
        tokens, related_tenant = self.service.validate_credentials(
            self.user.email, "password"
        )

        required_fields = ["refresh", "access"]
        for field in required_fields:
            self.assertIn(field, tokens)
            self.assertIsNotNone(tokens[field])

    def test_validate_credentials_user_is_not_verified(self):
        self.user.is_verified = False
        self.user.save()

        with self.assertRaises(UserNotVerifiedException):
            self.service.validate_credentials(self.user.email, "password")

    def test_validate_credentials_user_password_is_incorrect(self):
        self.user.set_password("wrong_password")
        self.user.save()

        with self.assertRaises(InvalidCredentialsException):
            self.service.validate_credentials(self.user.email, "password")

    def test_validate_credentials_user_is_not_active(self):
        self.user.is_active = False
        self.user.save()

        with self.assertRaises(UserNotActiveException):
            self.service.validate_credentials(self.user.email, "password")

    def test_validate_credentials_user_does_not_exist(self):
        with self.assertRaises(InvalidCredentialsException):
            self.service.validate_credentials("wrong@example.com", "password")

    def test_refresh_token_success(self):
        tokens = self.service.refresh_token(str(self.refresh_token))

        required_fields = ["refresh", "access"]
        for field in required_fields:
            self.assertIn(field, tokens)
            self.assertIsNotNone(tokens[field])

    def test_refresh_token_invalid_token(self):
        with self.assertRaises(InvalidTokenException):
            self.service.refresh_token("invalid_token")

    @patch("users.models.User.objects.create_user")
    def test_register_success(self, mock_create_user):
        mock_create_user.return_value = self.user
        result = self.service.register("test@example.com", "password")
        self.assertTrue(result)
        mock_create_user.assert_called_once()

    def test_register_user_already_exists(self):
        user = baker.make(User, email="test@example.com")
        user.set_password("password")
        user.is_verified = True
        user.save()

        with self.assertRaises(UserAlreadyExistsException):
            self.service.register("test@example.com", "password")

    def test_register_user_already_in_verification_process(self):
        user = baker.make(User, email="test@example.com")
        user.set_password("password")
        user.is_verified = False
        user.set_verification_code("123456")
        user.verification_code_expires_at = timezone.now() + timezone.timedelta(
            minutes=15
        )
        user.save()

        with self.assertRaises(UserIsAlreadyInVerificationProcessException):
            self.service.register("test@example.com", "password")

    def test_generate_verification_code(self):
        verification_code = self.service._generate_verification_code()
        self.assertIsNotNone(verification_code)
        self.assertEqual(len(verification_code), 6)

    def test_verify_email_success(self):
        user = baker.make(User, email="test@example.com")
        user.set_password("password")
        user.is_verified = False
        user.set_verification_code("123456")
        user.verification_code_expires_at = timezone.now() + timezone.timedelta(
            minutes=15
        )
        user.save()

        self.service.verify_email("test@example.com", "123456")
        user.refresh_from_db()
        self.assertEqual(user.is_verified, True)
        self.assertEqual(user.verification_code, "")
        self.assertEqual(user.verification_code_expires_at, None)
        self.assertIsNotNone(user.verification_code_verified_at)

    def test_verify_email_invalid_verification_code(self):
        user = baker.make(User, email="test@example.com")
        user.set_password("password")
        user.is_verified = False
        user.set_verification_code("123456")
        user.verification_code_expires_at = timezone.now() + timezone.timedelta(
            minutes=15
        )
        user.save()

        with self.assertRaises(InvalidVerificationCodeException):
            self.service.verify_email("test@example.com", "123457")

    def test_verify_email_user_already_verified(self):
        user = baker.make(User, email="test@example.com")
        user.set_password("password")
        user.is_verified = True
        user.save()

        with self.assertRaises(UserAlreadyVerifiedException):
            self.service.verify_email("test@example.com", "123456")

    def test_verify_invalid_credentials(self):
        with self.assertRaises(InvalidCredentialsException):
            self.service.verify_email("wrong@example.com", "123456")

    def test_resend_verification_email_success(self):
        user = baker.make(User, email="test@example.com")
        user.set_password("password")
        user.is_verified = False
        user.set_verification_code("123456")
        # Set expired verification code
        user.verification_code_expires_at = timezone.now() - timezone.timedelta(
            minutes=1
        )
        user.save()

        old_verification_code = user.verification_code
        old_expires_at = user.verification_code_expires_at

        result = self.service.resend_verification_email("test@example.com")

        self.assertTrue(result)
        user.refresh_from_db()
        self.assertIsNotNone(user.verification_code)
        self.assertNotEqual(user.verification_code, old_verification_code)
        self.assertIsNotNone(user.verification_code_expires_at)
        self.assertGreater(user.verification_code_expires_at, old_expires_at)
        self.assertGreater(user.verification_code_expires_at, timezone.now())

    def test_resend_verification_email_user_does_not_exist(self):
        with self.assertRaises(InvalidCredentialsException):
            self.service.resend_verification_email("nonexistent@example.com")

    def test_resend_verification_email_user_already_verified(self):
        user = baker.make(User, email="test@example.com")
        user.set_password("password")
        user.is_verified = True
        user.save()

        with self.assertRaises(UserAlreadyVerifiedException):
            self.service.resend_verification_email("test@example.com")

    def test_resend_verification_email_already_in_verification_process(self):
        user = baker.make(User, email="test@example.com")
        user.set_password("password")
        user.is_verified = False
        user.set_verification_code("123456")
        user.verification_code_expires_at = timezone.now() + timezone.timedelta(
            minutes=10
        )
        user.save()

        with self.assertRaises(UserIsAlreadyInVerificationProcessException):
            self.service.resend_verification_email("test@example.com")
