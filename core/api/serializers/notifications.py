from rest_framework import serializers
from apps.notification.models import Notification
from apps.supportticket.models import SupportTicket


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
            "is_deleted",
            "is_read",
            "read_at",
            "created_at",
        ]
        read_only_fields = fields

    def get_is_deleted(self, obj):
        ticket_alias = obj.data.get("ticket_alias")

        if not ticket_alias:
            return False

        ticket = SupportTicket.objects.filter(alias=ticket_alias).first()

        if ticket is None:
            return True

        return ticket.is_deleted