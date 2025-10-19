from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.exceptions import APIException


class CompanyAlreadyExistsException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Company with this name already exists")
    default_code = "companies_001"


class UserAlreadyHaveCompanyException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _(
        "You have a relation with a company. " "You cannot create a new company."
    )
    default_code = "companies_002"
