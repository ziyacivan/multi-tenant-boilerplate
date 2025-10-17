from django.db import models
from tenant_users.tenants.models import UserProfile


class User(UserProfile):
    manager = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True
    )
