from django.db import models
from django.utils.translation import gettext_lazy as _

from employees.choices import EmployeeGender, EmployeeRole
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
