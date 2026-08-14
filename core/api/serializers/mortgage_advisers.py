from rest_framework import serializers

from apps.property.models import (
    PropertyOwnership,
    MortgageAdviserPropertyPermission,
    MortgageAdviserMortgagePermission,
)
from apps.property.enums import PropertyOwnerType


class MortgageAdviserPropertyPermissionSlimSerializer(serializers.ModelSerializer):
    property = serializers.UUIDField(source="property.alias", read_only=True)
    mortgage_adviser = serializers.UUIDField(
        source="mortgage_adviser.alias", read_only=True
    )

    class Meta:
        model = MortgageAdviserPropertyPermission
        fields = [
            "mortgage_adviser",
            "property",
            "can_view",
            "can_edit",
        ]


class MortgageAdviserMortgagePermissionSlimSerializer(serializers.ModelSerializer):
    mortgage = serializers.UUIDField(source="mortgage.alias", read_only=True)
    mortgage_adviser = serializers.UUIDField(
        source="mortgage_adviser.alias", read_only=True
    )

    class Meta:
        model = MortgageAdviserMortgagePermission
        fields = [
            "mortgage_adviser",
            "mortgage",
            "can_view",
            "can_edit",
        ]


class MortgageAdviserPropertyPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MortgageAdviserPropertyPermission
        fields = [
            "can_view",
            "can_edit",
        ]


class MortgageAdviserMortgagePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MortgageAdviserMortgagePermission
        fields = [
            "can_view",
            "can_edit",
        ]


class PropertyOwnershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyOwnership
        fields = [
            "shareholder_name",
            "owner_name",
            "share_percentage",
        ]
        extra_kwargs = {
            "owner_name": {"required": False, "allow_null": True, "allow_blank": True},
            "shareholder_name": {
                "required": False,
                "allow_null": True,
                "allow_blank": True,
            },
            "share_percentage": {"required": False, "allow_null": True},
        }

    def to_representation(self, instance):
        rep = {}
        property_owner = getattr(instance.property, "property_owner", None)

        if property_owner == PropertyOwnerType.COMPANY:
            rep["shareholder_name"] = instance.shareholder_name
            rep["share_percentage"] = instance.share_percentage
        else:
            rep["owner_name"] = instance.owner_name

        return rep
