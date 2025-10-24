from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from employees.models import Employee
from employees.permissions import IsMinimumManagerOrReadOnly
from employees.serializers import EmployeeSerializer
from employees.services import EmployeeService


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all().order_by("-created_on")
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated, IsMinimumManagerOrReadOnly]
    service_class = EmployeeService()

    def perform_create(self, serializer):  # TODO: perform-create kapatmam lazım.
        serializer.instance = self.service_class.create_object(
            **serializer.validated_data
        )

    def perform_update(self, serializer):
        serializer.instance = self.service_class.update_object(
            serializer.instance, **serializer.validated_data
        )

    def perform_destroy(self, instance):
        force_delete = self.request.query_params.get("force", "false").lower() == "true"
        self.service_class.delete_object(instance, force_delete=force_delete)
