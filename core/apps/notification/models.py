from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.notification.enums import NotificationType
from apps.property.models import Tenant
from common.models import CreatedAtUpdatedAtBaseModel
from apps.authentication.models import User

class Notification(CreatedAtUpdatedAtBaseModel):
    recipient = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="user_notifications",
    )
    tenant = models.ForeignKey(
        Tenant,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="tenant_notifications",
    )
    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
    )
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        user = self.tenant or self.recipient
        return f"{user.email} - {self.notification_type}"

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])