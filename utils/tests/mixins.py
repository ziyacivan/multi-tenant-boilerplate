from typing import Type

from django.contrib.auth import get_user_model
from django.db import connection

from django_tenants.test.client import TenantClient
from django_tenants.utils import (
    get_public_schema_name,
    get_tenant_domain_model,
    get_tenant_model,
)
from model_bakery import baker
from rest_framework_simplejwt.tokens import RefreshToken

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


class AuthenticatedTenantTestMixin(TenantTestCaseMixin):
    """
    Mixin for testing tenant-specific views that require authentication.
    Provides JWT token generation and authenticated TenantClient setup.
    """

    def setUp(self):
        super().setUp()
        self.client = TenantClient(self.tenant)
        self.test_user = None
        self.test_employee = None
        self._auth_token = None

    def create_test_user(self, email="testuser@example.com", password="testpass123"):
        user = baker.make(TenantUser, email=email)
        user.set_password(password)
        user.is_active = True
        user.is_verified = True
        user.save()
        return user

    def create_test_employee(self, user=None, role="employee", **kwargs):
        from employees.models import Employee

        if user is None:
            user = self.create_test_user()

        employee_data = {
            "user": user,
            "first_name": kwargs.get("first_name", "Test"),
            "last_name": kwargs.get("last_name", "User"),
            "role": role,
            "is_active": True,
        }
        employee_data.update(kwargs)

        employee = Employee.objects.create(**employee_data)
        return employee

    def get_auth_token(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def authenticate_client(self, user=None, role="employee"):
        if user is None:
            user = self.create_test_user()

        self.test_user = user
        self.test_employee = self.create_test_employee(user=user, role=role)

        self._auth_token = self.get_auth_token(user)

        return self.test_user, self.test_employee

    def _add_auth_header(self, kwargs):
        if self._auth_token:
            kwargs.setdefault("HTTP_AUTHORIZATION", f"Bearer {self._auth_token}")
        return kwargs

    def get(self, *args, **kwargs):
        return self.client.get(*args, **self._add_auth_header(kwargs))

    def post(self, *args, **kwargs):
        return self.client.post(*args, **self._add_auth_header(kwargs))

    def put(self, *args, **kwargs):
        return self.client.put(*args, **self._add_auth_header(kwargs))

    def patch(self, *args, **kwargs):
        return self.client.patch(*args, **self._add_auth_header(kwargs))

    def delete(self, *args, **kwargs):
        return self.client.delete(*args, **self._add_auth_header(kwargs))
