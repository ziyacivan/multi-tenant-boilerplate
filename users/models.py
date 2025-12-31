import bcrypt
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

    def set_verification_code(self, raw_verification_code: str):
        hashed_code = bcrypt.hashpw(
            raw_verification_code.encode("utf-8"), bcrypt.gensalt()
        )
        self.verification_code = hashed_code.decode("utf-8")

    def check_verification_code(self, raw_verification_code: str) -> bool:
        if not self.verification_code:
            return False

        try:
            return bcrypt.checkpw(
                raw_verification_code.encode("utf-8"),
                self.verification_code.encode("utf-8"),
            )
        except ValueError:
            return False
