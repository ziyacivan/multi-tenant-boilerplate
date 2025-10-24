from rest_framework import permissions

from employees.choices import EmployeeRole
from employees.models import Employee


class IsMinimumManagerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True

        if request.method in permissions.SAFE_METHODS:
            return True

        try:
            employee_instance = Employee.objects.only("role").get(user=request.user)
        except Employee.DoesNotExist:
            return False

        return employee_instance.role in [EmployeeRole.manager, EmployeeRole.owner]


class CanManagePersonalDetail(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method == "POST":
            try:
                employee = request.user.employee
                return employee.role in [EmployeeRole.manager, EmployeeRole.owner]
            except Employee.DoesNotExist:
                return False

        return True

    def has_object_permission(self, request, view, obj):
        try:
            current_employee = request.user.employee
        except Employee.DoesNotExist:
            return False

        if current_employee.role in [EmployeeRole.owner, EmployeeRole.manager]:
            return True

        if current_employee.role == EmployeeRole.employee:
            return obj.id == current_employee.id

        return False
