from rest_framework import serializers

from employees.models import Employee, PersonalDetail


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


class PersonalDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalDetail
        fields = [
            "id",
            "employee",
            "address",
            "identification_number",
            "date_of_birth",
            "personal_phone",
            "is_married",
            "number_of_children",
            "graduation",
            "mandatory_military_service_completed",
            "driver_license",
            "disability_degree",
            "first_emergency_contact_name",
            "first_emergency_contact_phone",
            "second_emergency_contact_name",
            "second_emergency_contact_phone",
            "payroll_bank_account_no",
            "payroll_bank_account_iban",
            "payroll_bank_account_currency",
            "attributes",
            "created_on",
            "updated_on",
        ]
        read_only_fields = ["id", "employee", "created_on", "updated_on"]
