from rest_framework import serializers

from apps.property.models import Property, DocumentFile

from .models import Media


class PropertySlimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = ["id", "alias", "property_name"]


class MediaSlimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = [
            "id",
            "image",
            "description",
        ]


class DocumentFileSlimSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentFile
        fields = ["id", "file", "description"]
