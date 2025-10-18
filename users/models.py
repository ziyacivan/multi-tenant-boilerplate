from django.db import models
from django.utils.translation import gettext_lazy as _
from tenant_users.tenants.models import UserProfile

from utils.models import BaseModel


class User(BaseModel, UserProfile):
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
