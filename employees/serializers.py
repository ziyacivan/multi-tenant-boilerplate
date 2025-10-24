from rest_framework import serializers

from employees.models import Employee


class EmployeeSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Employee
        fields = [
            "id",
            "user",
            "email",
            "first_name",
            "last_name",
            "photo",
            "role",
            "manager",
            "gender",
            "is_active",
            "attributes",
            "created_on",
            "updated_on",
        ]
        read_only_fields = ["id", "user", "created_on", "updated_on"]


class EmployeeCreateSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
