from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions, status


class InvalidCredentialsException(exceptions.APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = _("Invalid credentials")
    default_code = "auth_001"


class UserNotActiveException(exceptions.APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = _("User is not active")
    default_code = "auth_002"
