from django.contrib.auth import get_user_model
from rest_framework import serializers
from apps.organisation.models import OrganisationUser
from apps.supportticket.models import (
    SupportTicketFile,
    SupportTicket,
    SupportTicketComment
)

User = get_user_model()


class SupportTicketUserSlimSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=255, source="get_full_name", read_only=True)
    user_type = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "alias",
            "profile_image",
            "name",
            "first_name",
            "last_name",
            "email",
            "user_type",
        ]

    def get_user_type(self, obj):
        organisation_user = OrganisationUser.objects.filter(user=obj).only("role").first()
        return organisation_user.role if organisation_user else None


class SupportTicketFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicketFile
        fields = ["alias", "file"]


def _delete_files_from_storage(queryset):
    """Delete both the DB rows and the underlying storage files."""
    for support_file in queryset:
        support_file.file.delete(save=False)
    queryset.delete()


class SupportTicketSerializer(serializers.ModelSerializer):
    created_by = SupportTicketUserSlimSerializer(read_only=True)
    files = SupportTicketFileSerializer(many=True, read_only=True)
    upload_files = serializers.ListField(
        child=serializers.FileField(), write_only=True, required=False
    )
    organisation = serializers.CharField(source="organisation.name", read_only=True)

    class Meta:
        model = SupportTicket
        fields = [
            "alias",
            "ticket_id",
            "ticket_type",
            "subject",
            "description",
            "upload_files",
            "files",
            "created_at",
            "created_by",
            "organisation",
        ]
        read_only_fields = [
            "alias",
            "ticket_id",
            "created_at",
            "created_by",
        ]

    def create(self, validated_data):
        upload_files = validated_data.pop("upload_files", [])
        ticket = SupportTicket.objects.create(**validated_data)

        for file in upload_files:
            SupportTicketFile.objects.create(ticket=ticket, file=file)

        return ticket

    def update(self, instance, validated_data):
        upload_files = validated_data.pop("upload_files", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if upload_files is not None:
            _delete_files_from_storage(instance.files.all())

            for file in upload_files:
                SupportTicketFile.objects.create(ticket=instance, file=file)

        return instance


class SupportTicketCommentSerializer(serializers.ModelSerializer):
    author = SupportTicketUserSlimSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    files = SupportTicketFileSerializer(many=True, read_only=True)
    upload_files = serializers.ListField(
        child=serializers.FileField(), write_only=True, required=False
    )

    class Meta:
        model = SupportTicketComment
        fields = [
            "id",
            "alias",
            "message",
            "parent",
            "author",
            "files",
            "upload_files",
            "replies",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "alias",
            "author",
            "created_at",
        ]

    def get_replies(self, obj):
        if obj.parent is None:
            replies = obj.replies.all().order_by("created_at")
            return SupportTicketCommentSerializer(
                replies, many=True, context=self.context
            ).data
        return []

    def validate(self, attrs):
        parent = attrs.get("parent")
        ticket = attrs.get("ticket") or getattr(self.instance, "ticket", None)
        if parent and ticket and parent.ticket_id != ticket.id:
            raise serializers.ValidationError(
                {"parent": "Parent comment must belong to the same ticket."}
            )
        return attrs

    def create(self, validated_data):
        upload_files = validated_data.pop("upload_files", [])
        comment = SupportTicketComment.objects.create(**validated_data)

        for file in upload_files:
            SupportTicketFile.objects.create(comment=comment, file=file)

        return comment