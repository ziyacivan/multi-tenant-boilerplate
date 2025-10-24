from typing import Type

from django.contrib.auth import get_user_model
from django.db import connection

from django_tenants.test.client import TenantClient
from django_tenants.utils import (
    get_public_schema_name,
    get_tenant_domain_model,
    get_tenant_model,
    tenant_context,
)
from model_bakery import baker
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from employees.choices import EmployeeRole
from employees.models import Employee
from users.models import User

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
        self.tenant_id = str(self.tenant.pk)
        self.client = APIClient()
        self._auth_token = None
        self.test_employee = None

    def authenticate_client(self, role: EmployeeRole = EmployeeRole.employee):
        user = self.create_test_user(email=f"test_{role}@test.com")

        self.test_employee = self.create_test_employee(user=user, role=role)

        refresh = RefreshToken.for_user(user)
        self._auth_token = str(refresh.access_token)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self._auth_token}")

    def create_test_user(self, email: str, **kwargs) -> User:
        with tenant_context(self.tenant):
            user = User.objects.create(email=email, **kwargs)
        return user

    def create_test_employee(
        self, user: User = None, role: EmployeeRole = EmployeeRole.employee, **kwargs
    ) -> Employee:
        if user is None:
            user = self.create_test_user(email="auto_generated@test.com")

        employee_data = {
            "user": user,
            "first_name": kwargs.pop("first_name", "Test"),
            "last_name": kwargs.pop("last_name", "Employee"),
            "role": role,
            **kwargs,
        }

        with tenant_context(self.tenant):
            employee = Employee.objects.create(**employee_data)

        return employee

    def get(self, path: str, **kwargs):
        kwargs.setdefault("HTTP_X_CLIENT", self.tenant_id)
        return self.client.get(path, **kwargs)

    def post(self, path: str, data=None, **kwargs):
        kwargs.setdefault("HTTP_X_CLIENT", self.tenant_id)
        return self.client.post(path, data, **kwargs)

    def put(self, path: str, data=None, **kwargs):
        kwargs.setdefault("HTTP_X_CLIENT", self.tenant_id)
        return self.client.put(path, data, **kwargs)

    def patch(self, path: str, data=None, **kwargs):
        kwargs.setdefault("HTTP_X_CLIENT", self.tenant_id)
        return self.client.patch(path, data, **kwargs)

    def delete(self, path: str, **kwargs):
        kwargs.setdefault("HTTP_X_CLIENT", self.tenant_id)
        return self.client.delete(path, **kwargs)
