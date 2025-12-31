from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from employees.permissions import IsMinimumManagerOrReadOnly
from titles.models import Title
from titles.serializers import TitleSerializer
from titles.services import TitleService


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.filter(is_active=True).order_by("-created_on")
    serializer_class = TitleSerializer
    permission_classes = [IsAuthenticated, IsMinimumManagerOrReadOnly]
    service_class = TitleService()

    def perform_create(self, serializer):
        serializer.instance = self.service_class.create_object(
            **serializer.validated_data
        )

    def perform_update(self, serializer):
        serializer.instance = self.service_class.update_object(
            instance=serializer.instance, **serializer.validated_data
        )

    def perform_destroy(self, instance):
        self.service_class.delete_object(instance=instance)
