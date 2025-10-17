from typing import Any

from django.db.models import QuerySet


class TenantRelatedMixin:
    def get_queryset(self) -> QuerySet[Any]:
        user_tenants = self.request.user.tenants.all().only("id")
        return (
            super()
            .get_queryset()
            .filter(id__in=user_tenants)
            .exclude(schema_name="public")
        )
