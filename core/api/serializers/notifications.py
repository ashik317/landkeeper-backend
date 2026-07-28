from rest_framework import serializers
from apps.notification.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source="get_notification_type_display", read_only=True)
    description = serializers.CharField(source="message", read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "title",
            "description",
            "data",
            "is_read",
            "read_at",
            "created_at",
        ]
        read_only_fields = fields