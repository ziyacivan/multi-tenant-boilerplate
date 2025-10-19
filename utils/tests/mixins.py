from typing import Type

from django.contrib.auth import get_user_model
from django.db import connection
from django_tenants.utils import (
    get_public_schema_name,
    get_tenant_domain_model,
    get_tenant_model,
)

Tenant = get_tenant_model()
Domain = get_tenant_domain_model()
TenantUser = get_user_model()


class TenantTestCaseMixin:
    @classmethod
    def setUpClass(cls):
        cls._ensure_public_tenant_exists()
        super().setUpClass()

    @classmethod
    def _ensure_public_tenant_exists(cls):
        public_schema_name = get_public_schema_name()

        connection.set_schema_to_public()

        if not Tenant.objects.filter(schema_name=public_schema_name).exists():
            public_owner = TenantUser(email="public@system.local")
            public_owner.set_password("system_password")
            public_owner.save()

            public_tenant = Tenant(
                schema_name=public_schema_name,
                name="Public Tenant",
                owner=public_owner,
            )
            public_tenant.save()

    @classmethod
    def setup_tenant(cls, tenant):
        owner_email = "owner@test.com"

        connection.set_schema_to_public()
        try:
            owner = TenantUser.objects.get(email=owner_email)
        except TenantUser.DoesNotExist:
            owner = TenantUser.objects.create_user(
                email=owner_email, password="password"
            )

        tenant.owner = owner

        if hasattr(super(), "setup_tenant"):
            super().setup_tenant(tenant)

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()
