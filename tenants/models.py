from django.db import models
from django.utils.translation import gettext_lazy as _
from django_tenants.models import DomainMixin
from tenant_users.tenants.models import TenantBase

from utils.models import BaseModel


class Client(BaseModel, TenantBase):
    name = models.CharField(_("name"), max_length=255)
    description = models.TextField(_("description"), blank=True)

    is_active = models.BooleanField(_("is active"), default=True)

    auto_create_schema = True
    auto_drop_schema = False

    def __str__(self):
        return self.name


class Domain(DomainMixin):
    pass
