from django.db import models
from django.utils.translation import gettext_lazy as _

from employees.choices import EmployeeContractType, EmployeeRole
from users.models import User
from utils.models import BaseModel


class Employee(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_("user"))
    first_name = models.CharField(_("first name"), max_length=255)
    last_name = models.CharField(_("last name"), max_length=255)
    photo = models.ImageField(
        _("photo"), upload_to="employees/photos/", null=True, blank=True
    )
    role = models.CharField(
        _("role"),
        max_length=20,
        choices=EmployeeRole.choices,
        default=EmployeeRole.employee,
    )
    manager = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("manager"),
    )
    employment_date = models.DateField(_("employment date"), null=True, blank=True)
    termination_date = models.DateField(_("termination date"), null=True, blank=True)
    identification_number = models.CharField(
        _("identification number"), max_length=255, blank=True
    )
    contract_type = models.CharField(
        _("contract type"),
        max_length=20,
        choices=EmployeeContractType.choices,
        default=EmployeeContractType.indefinite,
    )
    contract_end_date = models.DateField(_("contract end date"), null=True, blank=True)
    phone_number = models.CharField(_("phone number"), max_length=255, blank=True)
    business_phone_number = models.CharField(
        _("business phone number"), max_length=255, blank=True
    )

    class Meta:
        verbose_name = _("employee")
        verbose_name_plural = _("employees")
