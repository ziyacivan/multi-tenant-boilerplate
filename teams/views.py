from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from employees.permissions import IsMinimumManagerOrReadOnly
from teams.models import Team
from teams.serializers import TeamSerializer
from teams.services import TeamService


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.filter(is_active=True).order_by("-created_on")
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated, IsMinimumManagerOrReadOnly]
    service_class = TeamService()

    def perform_create(self, serializer):
        serializer.instance = self.service_class.create_object(
            **serializer.validated_data
        )

    def perform_update(self, serializer):
        serializer.instance = self.service_class.update_object(
            serializer.instance, **serializer.validated_data
        )

    def perform_destroy(self, instance):
        self.service_class.delete_object(instance)
