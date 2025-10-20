from rest_framework import permissions


class IsMinimumManagerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        from employees.choices import EmployeeRole
        from employees.models import Employee

        try:
            employee_instance = Employee.objects.only("role").get(user=request.user)
        except Employee.DoesNotExist:
            return False

        return employee_instance.role in [EmployeeRole.manager, EmployeeRole.owner]
