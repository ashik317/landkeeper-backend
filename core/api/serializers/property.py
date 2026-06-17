from rest_framework import serializers
from apps.property.models import Property
from common.models import Media


class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = [
            "id",
            "image",
            "description",
        ]

class PropertySerializer(serializers.ModelSerializer):
    images = MediaSerializer(many=True)

    class Meta:
        model = Property
        fields = [
            "alias",
            "name",
            "address",
            "property_type",
            "purchase_date",
            "purchase_price",
            "current_valuation",
            "ownership_type",
            "ownership_percentage",
            "images",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "alias",
            "created_at",
            "updated_at",
        ]