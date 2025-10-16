from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    manager = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return f"{self.get_full_name()}"
