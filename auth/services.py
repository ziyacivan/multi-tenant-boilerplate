from django.db.models import QuerySet
from rest_framework_simplejwt.tokens import RefreshToken

from auth.exceptions import InvalidCredentialsException, UserNotActiveException
from users.models import User


class AuthService:
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

        refresh = RefreshToken.for_user(user_instance)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

    @staticmethod
    def refresh_token(refresh_token: str) -> dict[str, str]:
        refresh = RefreshToken(refresh_token)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
