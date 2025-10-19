from django.db import transaction

from rest_framework.exceptions import APIException
from tenant_users.tenants.models import DeleteError
from tenant_users.tenants.tasks import provision_tenant

from tenants.exceptions import (
    CompanyAlreadyExistsException,
    UserAlreadyHaveCompanyException,
)
from tenants.models import Client, Domain
from users.models import User
from utils.interfaces import BaseService


class ClientService(BaseService):
    def create_object(
        self,
        name: str,
        description: str,
        slug: str,
        owner: User,
        legal_name: str,
        tax_no: str,
        tax_office: str,
        address: str,
        invoice_address: str,
        city: str,
        country: str,
        invoice_email_address: str,
        short_name: str,
        **kwargs: dict,
    ) -> Client:
        if Client.objects.filter(slug=slug).exists():
            raise CompanyAlreadyExistsException()

        if owner.tenants.count() > 1:
            raise UserAlreadyHaveCompanyException()

        tenant, domain = provision_tenant(
            tenant_name=name,
            tenant_slug=slug,
            owner=owner,
            is_staff=True,
            is_superuser=True,
        )
        tenant: Client = tenant
        tenant.description = description
        tenant.domain_url = domain.domain
        tenant.legal_name = legal_name
        tenant.tax_no = tax_no
        tenant.tax_office = tax_office
        tenant.address = address
        tenant.invoice_address = invoice_address
        tenant.city = city
        tenant.country = country
        tenant.invoice_email_address = invoice_email_address
        tenant.short_name = short_name
        tenant.save()
        return tenant

    def update_object(self, instance: Client, **kwargs) -> Client:
        _name = kwargs.pop("name", None)
        _slug = kwargs.pop("slug", None)
        _owner = kwargs.pop("owner", None)

        for key, value in kwargs.items():
            setattr(instance, key, value)
        instance.save(update_fields=kwargs.keys())
        return instance

    def delete_object(self, instance: Client):
        with transaction.atomic():
            tenant_users = instance.user_set.all()
            for tenant_user in tenant_users:
                tenant_user.is_active = False
            User.objects.bulk_update(tenant_users, ["is_active"])

            import time

            time_string = str(int(time.time()))
            new_domain_url = (
                f"{time_string}-{instance.owner.pk!s}-{instance.domain_url}"
            )
            instance.domain_url = new_domain_url
            instance.is_active = False
            instance.save()

            domain = Domain.objects.get(tenant=instance)
            domain.domain = instance.domain_url
            domain.save()

    def active_client(self, instance: Client):
        with transaction.atomic():
            instance.is_active = True
            instance.domain_url = instance.domain_url.split("-")[-1]
            instance.save()

            domain = Domain.objects.get(tenant=instance)
            domain.domain = instance.domain_url
            domain.save()

            tenant_users = instance.user_set.all()
            for tenant_user in tenant_users:
                tenant_user.is_active = True

            User.objects.bulk_update(tenant_users, ["is_active"])

            return instance
