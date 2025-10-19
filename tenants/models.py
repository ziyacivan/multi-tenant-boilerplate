from django.db import models
from django.utils.translation import gettext_lazy as _
from django_tenants.models import DomainMixin
from tenant_users.tenants.models import TenantBase

from utils.models import BaseModel


class Client(BaseModel, TenantBase):
    name = models.CharField(_("name"), max_length=255)
    description = models.TextField(_("description"), blank=True)
    legal_name = models.CharField(_("legal name"), max_length=255, blank=True)
    tax_no = models.CharField(_("tax number"), max_length=255, blank=True)
    tax_office = models.CharField(_("tax office"), max_length=255, blank=True)
    address = models.TextField(_("address"), blank=True)
    invoice_address = models.TextField(_("invoice address"), blank=True)
    city = models.CharField(_("city"), max_length=255, blank=True)
    country = models.CharField(_("country"), max_length=255, blank=True)
    invoice_email_address = models.EmailField(_("invoice email address"), blank=True)
    short_name = models.CharField(_("short name"), max_length=255, blank=True)

    is_active = models.BooleanField(_("is active"), default=True)

    auto_create_schema = True
    auto_drop_schema = False

    def __str__(self):
        return self.name


class Domain(DomainMixin):
    pass
