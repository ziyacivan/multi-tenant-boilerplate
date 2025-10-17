from django.db import models
from django.utils.translation import gettext_lazy as _


class UserRole(models.TextChoices):
    owner = "owner", _("Owner")
    manager = "manager", _("Manager")
    employee = "employee", _("Employee")
