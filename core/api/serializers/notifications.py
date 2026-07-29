from rest_framework import serializers
from apps.notification.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source="get_notification_type_display", read_only=True)
    description = serializers.CharField(source="message", read_only=True)
    is_deleted = serializers.SerializerMethodField()

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

    def get_is_deleted(self, obj):
        ticket = obj.support_ticket
        return ticket.is_deleted if ticket else False