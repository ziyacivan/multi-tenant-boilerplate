import random
import string

from django.db.models import QuerySet
from django.utils import timezone

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

        self.email_service.send_verification_email(
            email=email,
            verification_code=instance.verification_code,
            expires_at=instance.verification_code_expires_at,
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
        self.email_service.send_verification_email(
            email=email,
            verification_code=user.verification_code,
            expires_at=user.verification_code_expires_at,
        )
        return True
