from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from employees.mixins import MultiSerializerViewSetMixin
from employees.models import Employee
from employees.permissions import CanManagePersonalDetail, IsMinimumManagerOrReadOnly
from employees.serializers import (
    EmployeeCreateSerializer,
    EmployeeSerializer,
    PersonalDetailSerializer,
)
from employees.services import EmployeeService


class EmployeeViewSet(MultiSerializerViewSetMixin, viewsets.ModelViewSet):
    queryset = Employee.objects.select_related("user").all().order_by("-created_on")
    serializer_class = EmployeeSerializer
    serializer_action_classes = {
        "create": EmployeeCreateSerializer,
    }
    permission_classes = [IsAuthenticated, IsMinimumManagerOrReadOnly]
    service_class = EmployeeService()

    def perform_create(self, serializer):
        validated_data = serializer.validated_data
        serializer.instance = self.service_class.create_object(**validated_data)

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

    @extend_schema(
        summary="Manage Employee Personal Detail",
        description="Retrieve or update the personal detail information for a specific employee.",
        responses={200: PersonalDetailSerializer, 404: None},
    )
    @action(
        detail=True,
        methods=["get", "post", "patch"],
        url_path="personal-detail",
        permission_classes=[IsAuthenticated, CanManagePersonalDetail],
    )
    def personal_detail(self, request, pk: int | None = None):
        employee = self.get_object()
        personal_detail = self.service_class.get_personal_detail(employee)

        if request.method == "GET":
            return self._handle_get_personal_detail(personal_detail)

        return self._handle_create_or_update_personal_detail(
            employee, personal_detail, request
        )

    def _handle_get_personal_detail(self, personal_detail):
        if personal_detail is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = PersonalDetailSerializer(personal_detail)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def _handle_create_or_update_personal_detail(
        self, employee, personal_detail, request
    ):
        is_update = request.method == "PATCH"

        serializer = PersonalDetailSerializer(
            instance=personal_detail if is_update else None,
            data=request.data,
            partial=is_update,
        )
        serializer.is_valid(raise_exception=True)

        personal_detail = self.service_class.create_or_update_personal_detail(
            employee, **serializer.validated_data
        )

        response_serializer = PersonalDetailSerializer(personal_detail)
        response_status = status.HTTP_200_OK if is_update else status.HTTP_201_CREATED

        return Response(response_serializer.data, status=response_status)
