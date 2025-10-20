from django.db import models
from django.utils.translation import gettext_lazy as _


class EmployeeRole(models.TextChoices):
    owner = "owner", _("Owner")
    manager = "manager", _("Manager")
    employee = "employee", _("Employee")


class EmployeeGender(models.TextChoices):
    male = "male", _("Male")
    female = "female", _("Female")
    other = "other", _("Other")
