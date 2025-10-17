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
    first_name = models.CharField(_("first name"), max_length=255, blank=True)
    last_name = models.CharField(_("last name"), max_length=255, blank=True)

    verification_code = models.CharField(
        _("verification code"), max_length=255, blank=True
    )
    verification_code_expires_at = models.DateTimeField(
        _("verification code expires at"), null=True, blank=True
    )
    verification_code_verified_at = models.DateTimeField(
        _("verification code verified at"), null=True, blank=True
    )

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
