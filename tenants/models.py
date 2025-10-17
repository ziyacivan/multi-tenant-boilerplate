from django.db import models
from django_tenants.models import DomainMixin
from tenant_users.tenants.models import TenantBase

from utils.models import BaseModel


class Client(BaseModel, TenantBase):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    auto_create_schema = True
    auto_drop_schema = False

    def __str__(self):
        return self.name


class Domain(DomainMixin):
    pass
