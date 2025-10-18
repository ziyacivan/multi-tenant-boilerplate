from django.db import models
from django.utils.translation import gettext_lazy as _


class EmployeeRole(models.TextChoices):
    owner = "owner", _("Owner")
    manager = "manager", _("Manager")
    employee = "employee", _("Employee")


class EmployeeContractType(models.TextChoices):
    indefinite = "indefinite", _("Indefinite")
    limited = "limited", _("Limited")
