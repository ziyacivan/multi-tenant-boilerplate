from rest_framework import serializers

from titles.models import Title


class TitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Title
        fields = ["id", "name", "attributes", "created_on", "updated_on"]
        read_only_fields = ["is_active"]
