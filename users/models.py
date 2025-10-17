from django.db import models
from django.utils.translation import gettext_lazy as _
from tenant_users.tenants.models import UserProfile

from users.choices import UserRole
from utils.models import BaseModel


class User(BaseModel, UserProfile):
    manager = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("manager"),
    )
    role = models.CharField(
        _("role"),
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.employee,
    )

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
