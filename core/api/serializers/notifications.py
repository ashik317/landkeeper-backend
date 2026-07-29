from rest_framework import serializers
from apps.notification.models import Notification
from apps.supportticket.models import SupportTicket


class NotificationSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source="get_notification_type_display", read_only=True)
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
        data = dict(obj.data)

        if data.get("type") == "SUPPORT_TICKET":
            alias = data.get("alias")

            ticket = SupportTicket.objects.filter(alias=alias).first()

            data["is_deleted"] = (
                ticket.is_deleted if ticket else True
            )

        return data