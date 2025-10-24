from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

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

    @extend_schema(
        summary="Get Current User's Employee Record",
        description="Retrieve the employee record associated with the currently authenticated user.",
        responses={200: EmployeeSerializer},
    )
    @action(detail=False, methods=["get"], url_path="me", url_name="me")
    def get_current_user_employee(self, request):
        employee = self.service_class.get_employee_by_user(request.user)
        serializer = self.get_serializer(employee)
        return Response(serializer.data)
