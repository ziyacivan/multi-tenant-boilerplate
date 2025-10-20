from django.utils.translation import gettext_lazy as _

from rest_framework import status

from utils.exceptions import BaseAPIException


class CannotDeleteEmployeeException(BaseAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Cannot delete employee who is an owner of a tenant.")
    default_code = "emp_001"
