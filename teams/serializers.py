from rest_framework import serializers

from teams.models import Team


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ["id", "name", "parent", "description"]
        read_only_fields = ["id", "is_active", "created_on", "updated_on"]
