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
        user = attrs.get("user")
        property_obj = attrs.get("property")
        mortgage_obj = attrs.get("mortgage")

        # User explicitly changed can_view
        if "can_view" in attrs:
            can_view = attrs["can_view"]

            # If user turns view OFF,
            # automatically turn edit OFF.
            if can_view is False:
                attrs["can_edit"] = False

        # User explicitly changed can_edit
        if "can_edit" in attrs:
            can_edit = attrs["can_edit"]

            # If user turns edit ON,
            # automatically turn view ON.
            if can_edit is True:
                attrs["can_view"] = True

        # Property and mortgage cannot both be provided
        if property_obj is not None and mortgage_obj is not None:
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        "Permission cannot be assigned to both property and mortgage."
                    ]
                }
            )

        # Duplicate property permission
        if property_obj is not None:
            queryset = Permission.objects.filter(
                user=user,
                property=property_obj,
            )

            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise serializers.ValidationError(
                    {
                        "property": [
                            "This user already has permission for this property."
                        ]
                    }
                )

        # Duplicate mortgage permission
        if mortgage_obj is not None:
            queryset = Permission.objects.filter(
                user=user,
                mortgage=mortgage_obj,
            )

            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise serializers.ValidationError(
                    {
                        "mortgage": [
                            "This user already has permission for this mortgage."
                        ]
                    }
                )

        return attrs

    def to_representation(self, instance):
        rep = super().to_representation(instance)

        rep["user"] = UserSlimSerializer(
            instance.user,
            context={
                **self.context,
            },
        ).data

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
