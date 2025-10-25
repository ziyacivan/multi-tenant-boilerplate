from django.db import models

from utils.models import BaseModel


class Title(BaseModel):
    name = models.CharField(max_length=255, unique=True, db_index=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Title"
        verbose_name_plural = "Titles"
