from rest_framework import serializers
from apps.notification.models import Notification
from apps.notification.utils import enrich_notification_data


class NotificationSerializer(serializers.ModelSerializer):
    title = serializers.CharField(
        source="get_notification_type_display", read_only=True
    )
    description = serializers.CharField(source="message", read_only=True)
    data = serializers.SerializerMethodField()

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

    def get_data(self, obj):
        return enrich_notification_data(obj.data)
