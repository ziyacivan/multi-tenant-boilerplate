from rest_framework import serializers

from tenants.models import Client, Domain


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = [
            "id",
            "name",
            "description",
            "slug",
            "owner",
            "legal_name",
            "tax_no",
            "tax_office",
            "address",
            "invoice_address",
            "city",
            "country",
            "invoice_email_address",
            "short_name",
            "is_active",
            "created_on",
            "updated_on",
        ]
        read_only_fields = ["id", "owner", "is_active", "created_on", "updated_on"]


class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ["id", "domain", "tenant", "is_primary"]
        read_only_fields = ["id", "tenant", "domain", "is_primary"]
