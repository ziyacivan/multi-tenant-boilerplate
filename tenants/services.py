from django.db import transaction

from django_tenants.utils import schema_context
from tenant_users.tenants.tasks import provision_tenant

from employees.choices import EmployeeRole
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
        **kwargs: dict,
    ) -> Client:
        from employees.services import EmployeeService

        if Client.objects.filter(slug=slug).exists():
            raise CompanyAlreadyExistsException()

        if owner.tenants.count() > 1:
            raise UserAlreadyHaveCompanyException()

        tenant = Client(
            schema_name="{slug}".format(slug=slug),
            name=name,
            description=description,
            slug=slug,
            owner=owner,
            **kwargs,
        )
        tenant.save()

        domain = Domain()
        domain.domain = slug
        domain.tenant = tenant
        domain.is_primary = True
        domain.save()

        with schema_context(tenant.schema_name):
            employee_service = EmployeeService()
            employee_service.create_object(user=owner, role=EmployeeRole.owner)

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
