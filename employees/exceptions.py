from django.utils.translation import gettext_lazy as _

from rest_framework import status

from utils.exceptions import BaseAPIException


class CannotDeleteEmployeeException(BaseAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Cannot delete employee who is an owner of a tenant.")
    default_code = "emp_001"


class EmployeeNotFoundException(BaseAPIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = _("Employee record not found for the given user.")
    default_code = "emp_002"


class UserAlreadyExists(BaseAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("A user with the given email already exists.")
    default_code = "emp_003"
