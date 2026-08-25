from rest_framework import serializers

from apps.authentication.models import Permission, User
from apps.property.models import Property, Mortgage

from common.serializers import (
    UserSlimSerializer,
    PropertySlimSerializer,
)


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


class BulkPropertyPermissionSerializer(serializers.ModelSerializer):
    property = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
        write_only=True,
    )
    can_view = serializers.BooleanField(default=False)
    can_edit = serializers.BooleanField(default=False)

    class Meta:
        model = Permission
        fields = [
            "property",
            "property",
            "can_view",
            "can_edit",
        ]

    def to_representation(self, instance):
        rep = super().to_representation(instance)

        rep["property"] = PropertySlimSerializer(
            instance.property,
            context={
                **self.context,
            },
        ).data

        return rep

    def validate(self, attrs):
        if attrs["can_edit"] and not attrs["can_view"]:
            raise serializers.ValidationError(
                {"can_edit": "can_view must be true when can_edit is true."}
            )

        return attrs
