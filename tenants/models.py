from django.db import models
from django_tenants.models import TenantMixin, DomainMixin

from utils.models import BaseModel


class Client(BaseModel, TenantMixin):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    auto_create_schema = True
    auto_drop_schema = False

    def __str__(self):
        return self.name


class Domain(DomainMixin):
    pass
