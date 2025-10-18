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
        self, name: str, description: str, slug: str, owner: User
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
        try:
            tenant_users = instance.user_set.all()
            for tenant_user in tenant_users:
                tenant_user.is_active = False
            User.objects.bulk_update(tenant_users, ["is_active"])

            instance.delete_tenant()
            instance.is_active = False
            instance.save()

            domain = Domain.objects.get(tenant=instance)
            domain.domain = instance.domain_url
            domain.save()

        except DeleteError as e:
            raise APIException(detail=str(e))
