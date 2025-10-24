from django.db import transaction
from django.utils.translation import gettext_lazy as _

from employees.choices import EmployeeRole
from employees.exceptions import (
    CannotDeleteEmployeeException,
    EmployeeNotFoundException,
    UserAlreadyExists,
)
from employees.models import Employee, PersonalDetail
from tenants.services import ClientService
from users.models import User
from utils.interfaces import BaseService


class EmployeeService(BaseService):
    client_service = ClientService()

    def create_object(
        self,
        user: User = None,
        first_name: str = None,
        last_name: str = None,
        **kwargs: dict,
    ) -> Employee:
        if first_name is None and last_name is None:
            first_name = "John"
            last_name = "Doe"

        if user is None:
            from django_tenants.utils import schema_context

            with schema_context("public"):
                user = User.objects.filter(email=kwargs.get("email"))
                if user.exists():
                    raise UserAlreadyExists()

                user = User.objects.create_user(
                    email=kwargs.get("email"),
                )
                user.set_unusable_password()
                user.is_verified = False
                user.save()

            kwargs.pop("email", None)

        instance = Employee(
            user=user,
            first_name=first_name,
            last_name=last_name,
            **kwargs,
        )
        instance.save()
        return instance

    def update_object(self, instance: Employee, **kwargs: dict) -> Employee:
        kwargs.pop("is_active", None)

        for key, value in kwargs.items():
            setattr(instance, key, value)
        instance.save(update_fields=kwargs.keys())
        return instance

    def delete_object(self, instance: Employee, force_delete: bool | None) -> None:
        if instance.role == EmployeeRole.owner:
            raise CannotDeleteEmployeeException()

        if force_delete:
            instance.user.delete(force_drop=True)
            return

        instance.is_active = False
        instance.user.is_active = False
        instance.user.save(update_fields=["is_active"])
        instance.save(update_fields=["is_active"])

    @staticmethod
    def get_employee_by_user(user: User) -> Employee:
        try:
            employee = Employee.objects.get(user=user)
        except Employee.DoesNotExist:
            raise EmployeeNotFoundException()
        return employee

    @staticmethod
    def get_personal_detail(employee: Employee) -> PersonalDetail:
        try:
            return employee.personaldetail
        except PersonalDetail.DoesNotExist:
            return None

    @staticmethod
    def create_or_update_personal_detail(
        employee: Employee, **kwargs: dict
    ) -> PersonalDetail:
        with transaction.atomic():
            pd, _created = PersonalDetail.objects.get_or_create(employee=employee)
            for key, value in kwargs.items():
                setattr(pd, key, value)
            pd.save()
            return pd
