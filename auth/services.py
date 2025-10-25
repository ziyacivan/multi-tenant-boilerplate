import random
import string
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.db import transaction
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _

from rest_framework.request import Request
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
from auth.tasks import send_reset_email_task, send_verification_email_task
from tenants.models import Domain
from users.models import User
from utils.services import EmailService


class AuthService:
    VERIFICATION_CODE_LENGTH = 6
    VERIFICATION_CODE_EXPIRY_MINUTES = 15

    def __init__(self):
        self.email_service = EmailService()
        self.token_generator = PasswordResetTokenGenerator()

    @staticmethod
    def validate_credentials(email: str, password: str) -> dict[str, str]:
        try:
            user = User.objects.get(email=email)

            if not user.check_password(password):
                raise InvalidCredentialsException()

            if not user.is_active:
                raise UserNotActiveException()

            if not user.is_verified:
                raise UserNotVerifiedException()

            refresh = RefreshToken.for_user(user)
            return {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }, user.tenants.last()
        except User.DoesNotExist:
            raise InvalidCredentialsException()

    @staticmethod
    def refresh_token(refresh_token: str) -> dict[str, str]:
        try:
            refresh = RefreshToken(refresh_token)
            return {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }
        except Exception as e:
            raise InvalidTokenException() from e

    def register(self, email: str, password: str) -> bool:
        existing_user = User.objects.filter(email=email).first()
        if existing_user:
            if not existing_user.is_verified:
                raise UserIsAlreadyInVerificationProcessException(
                    verification_code_expires_at=existing_user.verification_code_expires_at,
                    is_verified=existing_user.is_verified,
                )
            raise UserAlreadyExistsException()

        raw_verification_code = self._generate_verification_code()

        extra_fields = {
            "is_active": False,
            "verification_code_expires_at": timezone.now()
            + timedelta(minutes=self.VERIFICATION_CODE_EXPIRY_MINUTES),
        }
        user = User.objects.create_user(email=email, password=password, **extra_fields)
        user.set_verification_code(raw_verification_code)
        user.save(update_fields=["verification_code"])

        send_verification_email_task.delay(
            email, raw_verification_code, user.verification_code_expires_at
        )
        return True

    @staticmethod
    def _generate_verification_code() -> str:
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

    @staticmethod
    def _is_valid_verification_code(user: User, verification_code: str) -> bool:
        """Check if verification code is valid."""
        return (
            user.verification_code
            and user.check_verification_code(verification_code)
            and user.verification_code_expires_at
            and timezone.now() <= user.verification_code_expires_at
        )

    @transaction.atomic
    def verify_email(self, email: str, verification_code: str) -> dict[str, str]:
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise InvalidCredentialsException()

        if user.is_verified:
            raise UserAlreadyVerifiedException()

        if not self._is_valid_verification_code(user, verification_code):
            raise InvalidVerificationCodeException()

        user.is_verified = True
        user.is_active = True
        user.verification_code_verified_at = timezone.now()
        user.verification_code = ""
        user.verification_code_expires_at = None
        user.save()

        return {"email": email, "is_verified": user.is_verified}

    @transaction.atomic
    def resend_verification_email(self, email: str) -> bool:
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise InvalidCredentialsException()

        if user.is_verified:
            raise UserAlreadyVerifiedException()

        if (
            user.verification_code_expires_at
            and timezone.now() < user.verification_code_expires_at
        ):
            raise UserIsAlreadyInVerificationProcessException()

        raw_verification_code = self._generate_verification_code()
        user.set_verification_code(raw_verification_code)
        user.verification_code_expires_at = timezone.now() + timedelta(
            minutes=self.VERIFICATION_CODE_EXPIRY_MINUTES
        )
        user.save()

        send_verification_email_task.delay(
            email, raw_verification_code, user.verification_code_expires_at
        )
        return True

    @staticmethod
    def _get_user_from_uidb64(uidb64: str) -> User | None:
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            return User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return None

    @staticmethod
    def _build_reset_url(uid: str, token: str) -> str:
        return f"{settings.FRONTEND_URL}/onboarding/employee/{uid}/{token}"

    def request_password_reset(self, email: str, request: Request):
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = self.token_generator.make_token(user)

        reset_url = self._build_reset_url(uid, token)
        send_reset_email_task.delay(user.id, reset_url)

    @transaction.atomic
    def confirm_password_reset(
        self, uidb64: str, token: str, new_password: str
    ) -> tuple[bool, str]:
        user = self._get_user_from_uidb64(uidb64)

        if user is not None and self.token_generator.check_token(user, token):
            user.set_password(new_password)
            user.save()
            return True, _("Password has been reset successfully.")

        return False, _("The reset link is invalid or has expired.")
