from employees.choices import EmployeeRole
from employees.exceptions import CannotDeleteEmployeeException
from employees.models import Employee
from tenants.models import Client
from tenants.services import ClientService
from users.models import User
from utils.interfaces import BaseService


class EmployeeService(BaseService):
    client_service = ClientService()

    def create_object(
        self, user: User, first_name: str, last_name: str, **kwargs: dict
    ) -> Employee:
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
