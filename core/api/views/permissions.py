from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    CreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.exceptions import NotFound, ValidationError

from apps.authentication.models import Permission
from apps.organisation.models import OrganisationUser
from apps.property.models import (
    Property,
    Mortgage,
)

from ..serializers.permissions import (
    PermissionSerializer,
    BulkPropertyPermissionSerializer,
)

from common.permission import (
    IsLandlord,
    IsAdmin,
)

User = get_user_model()


class PermissionListAPIView(CreateAPIView):
    permission_classes = [IsLandlord | IsAdmin]
    serializer_class = PermissionSerializer

    def get_organisation(self):
        organisation = self.request.user.get_organisation()

        if not organisation:
            raise NotFound("Organisation not found for the user.")

        return organisation

    def get_queryset(self):
        organisation = self.get_organisation()

        return Permission.objects.filter(organisation=organisation)

    def perform_create(self, serializer):
        organisation = self.get_organisation()

        serializer.save(organisation=organisation)


class PermissionDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsLandlord | IsAdmin]
    serializer_class = PermissionSerializer

    def get_organisation(self):
        organisation = self.request.user.get_organisation()

        if not organisation:
            raise NotFound("Organisation not found for the user.")

        return organisation

    def get_object(self):
        permission_alias = self.kwargs.get("permission_alias")
        organisation = self.get_organisation()

        return get_object_or_404(
            Permission,
            alias=permission_alias,
            organisation=organisation,
        )


class PropertyPermissionListAPIView(ListAPIView):
    permission_classes = [IsLandlord | IsAdmin]
    serializer_class = PermissionSerializer

    def get_organisation(self):
        organisation = self.request.user.get_organisation()

        if not organisation:
            raise NotFound("Organisation not found for the user.")

        return organisation

    def get_queryset(self):
        property_alias = self.kwargs.get("property_alias")
        organisation = self.get_organisation()

        property_obj = get_object_or_404(
            Property,
            alias=property_alias,
            organisation=organisation,
        )

        return Permission.objects.filter(
            property=property_obj,
            organisation=organisation,
        ).order_by("-created_at")


class MortgagePermissionListAPIView(ListAPIView):
    permission_classes = [IsLandlord | IsAdmin]
    serializer_class = PermissionSerializer

    def get_organisation(self):
        organisation = self.request.user.get_organisation()

        if not organisation:
            raise NotFound("Organisation not found for the user.")

        return organisation

    def get_queryset(self):
        mortgage_alias = self.kwargs.get("mortgage_alias")
        organisation = self.get_organisation()

        mortgage_obj = get_object_or_404(
            Mortgage,
            alias=mortgage_alias,
            organisation=organisation,
        )

        return Permission.objects.filter(
            mortgage=mortgage_obj,
            organisation=organisation,
        ).order_by("-created_at")


class BulkPropertyPermissionView(ListCreateAPIView):
    serializer_class = BulkPropertyPermissionSerializer
    permission_classes = [IsLandlord]

    def get_queryset(self):
        organisation = self.request.user.get_organisation()

        if not organisation:
            raise NotFound("Organisation not found for the user.")

        user_alias = self.kwargs.get("user_alias")
        user = get_object_or_404(
            User,
            alias=user_alias,
        )

        return Permission.objects.filter(
            organisation=organisation,
            user=user,
            property__isnull=False,
        ).order_by("-created_at")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        organisation = request.user.get_organisation()

        if not organisation:
            raise NotFound("Organisation not found for the user.")

        user = get_object_or_404(
            User,
            alias=self.kwargs.get("user_alias"),
        )

        property_aliases = serializer.validated_data["property"]

        properties = Property.objects.filter(
            alias__in=property_aliases,
            organisation=organisation,
        )

        if properties.count() != len(set(property_aliases)):
            raise ValidationError(
                {"property": ("One or more properties were not found.")}
            )

        can_view = serializer.validated_data["can_view"]
        can_edit = serializer.validated_data["can_edit"]

        with transaction.atomic():

            for property_obj in properties:

                # Find existing adviser assignment
                existing_permission = (
                    Permission.objects.filter(
                        organisation=organisation,
                        property=property_obj,
                    )
                    .exclude(user=user)
                    .first()
                )

                if existing_permission:
                    raise ValidationError(
                        {
                            "property": (
                                f"Property '{property_obj.property_name}' "
                                "is already assigned to another "
                                "user."
                            )
                        }
                    )

                # Create/update new adviser permission
                Permission.objects.update_or_create(
                    organisation=organisation,
                    user=user,
                    property=property_obj,
                    defaults={
                        "can_view": can_view,
                        "can_edit": can_edit,
                        "mortgage": None,
                    },
                )

        return Response(
            {
                "message": ("Property permissions updated successfully."),
                "user": user.alias,
                "properties_count": properties.count(),
            },
            status=status.HTTP_200_OK,
        )
