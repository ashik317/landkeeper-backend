from rest_framework import serializers

from apps.authentication.models import Permission, User
from apps.property.models import PropertyOwnership, Property, Mortgage
from apps.property.enums import PropertyOwnerType

from common.serializers import UserSlimSerializer


class PermissionSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        slug_field="alias",
        queryset=User.objects.all(),
    )

    property = serializers.SlugRelatedField(
        slug_field="alias",
        queryset=Property.objects.all(),
        required=False,
        allow_null=True,
        default=None,
    )

    mortgage = serializers.SlugRelatedField(
        slug_field="alias",
        queryset=Mortgage.objects.all(),
        required=False,
        allow_null=True,
        default=None,
    )

    class Meta:
        model = Permission
        fields = [
            "alias",
            "user",
            "property",
            "mortgage",
            "can_view",
            "can_edit",
        ]

    def validate(self, attrs):
        property_obj = attrs.get("property")
        mortgage_obj = attrs.get("mortgage")

        # Cannot have both
        if property_obj is not None and mortgage_obj is not None:
            raise serializers.ValidationError(
                "Permission cannot be assigned to both property and mortgage."
            )

        # Must have one
        if property_obj is None and mortgage_obj is None:
            raise serializers.ValidationError(
                "Either property or mortgage must be provided."
            )

        return attrs

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["user"] = UserSlimSerializer(instance.user).data
        return rep


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
