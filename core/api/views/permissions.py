from django.shortcuts import get_object_or_404

from rest_framework.generics import (
    ListAPIView,
    CreateAPIView,
    RetrieveUpdateAPIView,
)
from rest_framework.exceptions import NotFound

from apps.authentication.models import Permission
from apps.property.models import (
    Property,
    Mortgage,
)

from ..serializers.permissions import PermissionSerializer

from common.permission import (
    IsLandlord,
    IsAdmin,
)


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


class PermissionDetailView(RetrieveUpdateAPIView):
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
        )


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
        )
