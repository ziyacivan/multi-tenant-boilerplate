from django.db import models
from django.utils.translation import gettext_lazy as _


class BaseModel(models.Model):
    created_on = models.DateTimeField(_("created on"), auto_now_add=True)
    updated_on = models.DateTimeField(_("updated on"), auto_now=True)

    attributes = models.JSONField(_("attributes"), default=dict, blank=True)

    class Meta:
        abstract = True
