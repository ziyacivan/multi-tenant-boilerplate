from django.db import models
from django.utils.translation import gettext_lazy as _


class UserRole(models.TextChoices):
    system_admin = "system_admin", _("System Admin")
    system_user = "system_user", _("System User")
    owner = "owner", _("Owner")
    manager = "manager", _("Manager")
    employee = "employee", _("Employee")
