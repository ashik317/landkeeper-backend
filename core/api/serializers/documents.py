from rest_framework import serializers
from apps.document.models import Document, DocumentFile


def humanize_size(num_bytes: int | None) -> str:
    size = float(num_bytes or 0)
    units = ("B", "KB", "MB", "GB", "TB")

    for unit in units:
        if size < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{size:.0f} {unit}"

            return f"{size:.1f} {unit}".rstrip("0").rstrip(".")

        size /= 1024

    return "0 B"


class DocumentSerializer(serializers.ModelSerializer):
    size = serializers.SerializerMethodField()
    file = serializers.FileField(write_only=True)

    class Meta:
        model = Document
        fields = [
            "alias",
            "title",
            "category",
            "size",
            "created_at",
            "file",
        ]
        read_only_fields = [
            "alias",
            "size",
            "created_at",
        ]

    def get_size(self, obj):
        document_file = getattr(obj, "file", None)
        uploaded_file = getattr(document_file, "file", None)
        if not uploaded_file:
            return "0 B"
        return humanize_size(uploaded_file.size)

    def create(self, validated_data):
        uploaded_file = validated_data.pop("file")
        user = self.context["request"].user

        document_file = DocumentFile.objects.create(
            file=uploaded_file,
            created_by=user,
            updated_by=user,
        )

        return Document.objects.create(
            organisation=user.get_organisation(),
            uploaded_by=user,
            created_by=user,
            updated_by=user,
            file=document_file,
            **validated_data,
        )

    def update(self, instance, validated_data):
        uploaded_file = validated_data.pop("file", None)
        user = self.context["request"].user

        for field, value in validated_data.items():
            setattr(instance, field, value)

        instance.updated_by = user
        instance.save()

        if uploaded_file:
            instance.file.file = uploaded_file
            instance.file.updated_by = user
            instance.file.save(
                update_fields=[
                    "file",
                    "updated_by",
                ]
            )

        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        document_file = getattr(instance, "file", None)
        uploaded_file = getattr(document_file, "file", None)

        if not uploaded_file:
            representation["file"] = None
            return representation

        request = self.context.get("request")

        representation["file"] = (
            request.build_absolute_uri(uploaded_file.url)
            if request
            else uploaded_file.url
        )

        return representation