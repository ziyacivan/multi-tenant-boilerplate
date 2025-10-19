import random
import string

from django.conf import settings
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.db.models import QuerySet
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
from auth.tasks import send_verification_email_task
from tenants.models import Domain
from users.models import User
from utils.services import EmailService


class AuthService:
    email_service = EmailService()

    @staticmethod
    def validate_credentials(email: str, password: str) -> dict[str, str]:
        user_qs: QuerySet[User] = User.objects.filter(email=email)
        if not user_qs.exists():
            raise InvalidCredentialsException()

        user_instance: User = user_qs.first()
        if not user_instance.is_active:
            raise UserNotActiveException()

        if not user_instance.check_password(password):
            raise InvalidCredentialsException()

        if not user_instance.is_verified:
            raise UserNotVerifiedException()

        refresh = RefreshToken.for_user(user_instance)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

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
        user: User | None = User.objects.filter(email=email).first()
        if user:
            if user.is_verified is False:
                raise UserIsAlreadyInVerificationProcessException(
                    verification_code_expires_at=user.verification_code_expires_at,
                    is_verified=user.is_verified,
                )

            raise UserAlreadyExistsException()

        from django.db import connection

        connection.set_schema_to_public()

        instance: User = User.objects.create_user(email=email, password=password)
        instance.verification_code = self.generate_verification_code()
        instance.verification_code_expires_at = timezone.now() + timezone.timedelta(
            minutes=15
        )
        instance.is_active = False
        instance.is_verified = False
        instance.save()

        send_verification_email_task.delay(
            email, instance.verification_code, instance.verification_code_expires_at
        )
        return True

    @staticmethod
    def generate_verification_code() -> str:
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

    @staticmethod
    def verify_email(email: str, verification_code: str) -> dict[str, str]:
        user_qs: QuerySet[User] = User.objects.filter(email=email)
        if not user_qs.exists():
            raise InvalidCredentialsException()

        user: User = user_qs.first()

        if user.is_verified:
            raise UserAlreadyVerifiedException()

        if (
            not user.verification_code
            or user.verification_code != verification_code
            or not user.verification_code_expires_at
            or timezone.now() > user.verification_code_expires_at
        ):
            raise InvalidVerificationCodeException()

        user.is_verified = True
        user.is_active = True
        user.verification_code_verified_at = timezone.now()
        user.verification_code = ""
        user.verification_code_expires_at = None
        user.save()

        return {"email": email, "is_verified": user.is_verified}

    def resend_verification_email(self, email: str) -> bool:
        user_qs: QuerySet[User] = User.objects.filter(email=email)
        if not user_qs.exists():
            raise InvalidCredentialsException()

        user: User = user_qs.first()
        if user.is_verified:
            raise UserAlreadyVerifiedException()

        if (
            user.verification_code_expires_at
            and timezone.now() < user.verification_code_expires_at
        ):
            raise UserIsAlreadyInVerificationProcessException()

        user.verification_code = self.generate_verification_code()
        user.verification_code_expires_at = timezone.now() + timezone.timedelta(
            minutes=15
        )
        user.save()
        send_verification_email_task.delay(
            email, user.verification_code, user.verification_code_expires_at
        )
        return True

    @staticmethod
    def _get_user_from_uidb64(uidb64: str) -> User | None:
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            return user
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return None

    def request_password_reset(self, email: str, request: Request):
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return

        token_generator = PasswordResetTokenGenerator()
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)

        current_domain = request.get_host().split(":")[0]
        scheme = "https" if not settings.DEBUG else "http"

        try:
            domain_object = Domain.objects.get(domain=current_domain)
            tenant_domain = domain_object.domain
        except Domain.DoesNotExist:
            tenant_domain = settings.TENANT_USERS_DOMAIN

        frontend_reset_url = (
            f"{scheme}://{tenant_domain}:3000/reset-password/{uid}/{token}"
        )

        self.email_service.send_reset_email(user, frontend_reset_url)

    def confirm_password_reset(
        self, uidb64: str, token: str, new_password: str
    ) -> tuple[bool, str]:
        user = self._get_user_from_uidb64(uidb64)
        token_generator = PasswordResetTokenGenerator()

        if user is not None and token_generator.check_token(user, token):
            user.set_password(new_password)
            user.save()
            return True, _("Password has been reset successfully.")

        return False, _("The reset link is invalid or has expired.")
