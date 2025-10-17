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


class UserAlreadyExistsException(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("User already exists")
    default_code = "auth_003"


class InvalidVerificationCodeException(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Invalid or expired verification code")
    default_code = "auth_004"


class UserAlreadyVerifiedException(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("User is already verified")
    default_code = "auth_005"


class UserIsAlreadyInVerificationProcessException(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("User is already in verification process")
    default_code = "auth_006"
