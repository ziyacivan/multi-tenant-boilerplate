from django.utils.translation import gettext_lazy as _
from rest_framework import status

from utils.exceptions import BaseAPIException


class InvalidCredentialsException(BaseAPIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = _("Invalid credentials")
    default_code = "auth_001"


class UserNotActiveException(BaseAPIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = _("User is not active")
    default_code = "auth_002"


class UserAlreadyExistsException(BaseAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("User already exists")
    default_code = "auth_003"


class InvalidVerificationCodeException(BaseAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Invalid or expired verification code")
    default_code = "auth_004"


class UserAlreadyVerifiedException(BaseAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("User is already verified")
    default_code = "auth_005"


class UserIsAlreadyInVerificationProcessException(BaseAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _(
        "User is already in verification process. "
        "Verification email has been sent recently."
    )
    default_code = "auth_006"


class UserNotVerifiedException(BaseAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("User is not verified")
    default_code = "auth_007"
