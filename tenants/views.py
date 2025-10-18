from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from tenants.models import Client
from tenants.serializers import ClientSerializer
from tenants.services import ClientService
from utils.mixins import TenantRelatedMixin


class ClientViewSet(TenantRelatedMixin, viewsets.ModelViewSet):
    queryset = Client.objects.all().order_by("-created_on")
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]
    service_class = ClientService()

    def perform_create(self, serializer):
        owner = self.request.user
        serializer.instance = self.service_class.create_object(
            owner=owner, **serializer.validated_data
        )

    def perform_update(self, serializer):
        serializer.instance = self.service_class.update_object(
            serializer.instance, **serializer.validated_data
        )

    def perform_destroy(self, instance: Client):
        self.service_class.delete_object(instance=instance)
