from django.db import models
from django.utils.translation import gettext_lazy as _

from employees.choices import EmployeeGender, EmployeeRole
from users.models import User
from utils.models import BaseModel
from utils.storages import TenantFileSystemStorage


class Employee(BaseModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, verbose_name=_("user"), db_index=True
    )
    first_name = models.CharField(_("first name"), max_length=255)
    last_name = models.CharField(_("last name"), max_length=255)
    photo = models.ImageField(
        _("photo"),
        upload_to="employees/photos/",
        storage=TenantFileSystemStorage(),
        null=True,
        blank=True,
    )
    role = models.CharField(
        _("role"),
        max_length=20,
        choices=EmployeeRole.choices,
        default=EmployeeRole.employee,
    )
    gender = models.CharField(
        _("gender"),
        max_length=20,
        choices=EmployeeGender.choices,
        default=EmployeeGender.male,
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(_("is active"), default=True)

    class Meta:
        verbose_name = _("employee")
        verbose_name_plural = _("employees")

    @property
    def email(self):
        return self.user.email


class PersonalDetail(BaseModel):
    employee = models.OneToOneField(
        "employees.Employee", on_delete=models.CASCADE, verbose_name="employee"
    )
    address = models.CharField(max_length=255, null=True, blank=True)
    identification_number = models.CharField(
        max_length=11, unique=True, null=True, blank=True, db_index=True
    )
    date_of_birth = models.DateField(null=True, blank=True, db_index=True)
    personal_phone = models.CharField(
        max_length=20, unique=True, null=True, blank=True, db_index=True
    )
    is_married = models.BooleanField(default=False)
    number_of_children = models.PositiveSmallIntegerField(default=0)
    graduation = models.CharField(max_length=255, null=True, blank=True)
    mandatory_military_service_completed = models.BooleanField(default=False)
    driver_license = models.CharField(max_length=20, null=True, blank=True)
    disability_degree = models.PositiveSmallIntegerField(null=True, blank=True)
    first_emergency_contact_name = models.CharField(
        max_length=255, null=True, blank=True
    )
    first_emergency_contact_phone = models.CharField(
        max_length=20, null=True, blank=True
    )
    second_emergency_contact_name = models.CharField(
        max_length=255, null=True, blank=True
    )
    second_emergency_contact_phone = models.CharField(
        max_length=20, null=True, blank=True
    )
    payroll_bank_account_no = models.CharField(max_length=34, null=True, blank=True)
    payroll_bank_account_iban = models.CharField(
        max_length=34, unique=True, null=True, blank=True, db_index=True
    )
    payroll_bank_account_currency = models.CharField(
        max_length=3, null=True, blank=True
    )

    class Meta:
        verbose_name = "personal detail"
        verbose_name_plural = "personal details"
        indexes = [
            models.Index(
                fields=["identification_number", "date_of_birth"],
                name="personal_id_dob_idx",
            ),
        ]
