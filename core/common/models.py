from django.db import models
import os
import uuid
import logging
import pprint
import datetime

from django.conf import settings
from django.db import models

logger = logging.getLogger(__name__)
USER_IP_ADDRESS = ""
User = settings.AUTH_USER_MODEL

class CreatedAtUpdatedAtBaseModel(models.Model):
    alias = models.UUIDField(
        default=uuid.uuid4, editable=False, db_index=True, unique=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_%(class)s_set",
        verbose_name="Created By",
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_%(class)s_set",
        verbose_name="Updated By",
    )

    user_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        editable=False,
    )

    class Meta:
        abstract = True
        ordering = ("-created_at",)

    def _print(self):
        _pp = pprint.PrettyPrinter(indent=4)
        _pp.pprint("------------------------------------------")
        logger.info("Details of {} : ".format(self))
        _pp.pprint(vars(self))
        _pp.pprint("------------------------------------------")

    def save(self, *args, **kwargs):
        self.full_clean()
        self.user_ip = USER_IP_ADDRESS
        super().save(*args, **kwargs)