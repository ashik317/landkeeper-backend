from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView
from rest_framework.exceptions import NotFound, ValidationError

from apps.organisation.models import OrganisationUser
from apps.organisation.enums import OrganisationRoleChoices
from apps.property.models import (
    Property,
    Mortgage,
    MortgageAdviserPropertyPermission,
    MortgageAdviserMortgagePermission,
)

from ..serializers.mortgage_advisers import (
    MortgageAdviserPropertyPermissionSerializer,
    MortgageAdviserMortgagePermissionSerializer,
    MortgageAdviserPropertySerializer,
    MortgageAdviserMortgageSerializers,
    MortgageAdviserPropertyPermissionSlimSerializer,
    MortgageAdviserMortgagePermissionSlimSerializer,
)

from common.permission import (
    IsLandlord,
    IsMortgageAdviser,
    CanAccessMortgageAdviserProperty,
    CanAccessMortgageAdviserMortgage,
)

User = get_user_model()

class MortgageAdviserPropertyPermissionListAPIView(ListAPIView):
    permission_classes = [IsLandlord]
    serializer_class = MortgageAdviserPropertyPermissionSlimSerializer

    def get_queryset(self):
        organisation = self.request.user.get_organisation()

        if not organisation:
            raise NotFound("Organisation not found for the user.")

        return MortgageAdviserPropertyPermission.objects.filter(
            organisation=organisation,
        ).select_related("property", "mortgage_adviser")


class MortgageAdviserPropertyPermissionView(RetrieveUpdateAPIView):
    permission_classes = [IsLandlord]
    serializer_class = MortgageAdviserPropertyPermissionSerializer

    def get_organisation(self):
        organisation = self.request.user.get_organisation()

        if not organisation:
            raise NotFound("Organisation not found for the user.")

        return organisation

    def get_property(self, organisation):
        return get_object_or_404(
            Property,
            alias=self.kwargs["property_alias"],
            organisation=organisation,
        )

    def get_mortgage_adviser(self, organisation):
        adviser = get_object_or_404(
            User,
            alias=self.kwargs["adviser_alias"],
        )

        is_mortgage_adviser = OrganisationUser.objects.filter(
            user=adviser,
            organisation=organisation,
            role=OrganisationRoleChoices.MORTGAGE_ADVISER,
        ).exists()

        if not is_mortgage_adviser:
            raise ValidationError(
                "The selected user is not a mortgage adviser in this organisation."
            )

        return adviser

    def get_object(self):
        organisation = self.get_organisation()
        property_obj = self.get_property(organisation)
        adviser = self.get_mortgage_adviser(organisation)

        permission, _ = MortgageAdviserPropertyPermission.objects.get_or_create(
            mortgage_adviser=adviser,
            property=property_obj,
            organisation=organisation,
        )

        return permission

    def update(self, request, *args, **kwargs):
        permission = self.get_object()

        serializer = self.get_serializer(
            permission,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

class MortgageAdviserMortgagePermissionListAPIView(ListAPIView):
    permission_classes = [IsLandlord]
    serializer_class = MortgageAdviserMortgagePermissionSlimSerializer

    def get_queryset(self):
        organisation = self.request.user.get_organisation()

        if not organisation:
            raise NotFound("Organisation not found for the user.")

        return MortgageAdviserMortgagePermission.objects.filter(
            organisation=organisation,
        ).select_related("mortgage", "mortgage_adviser")



class MortgageAdviserMortgagePermissionView(RetrieveUpdateAPIView):
    permission_classes = [IsLandlord]
    serializer_class = MortgageAdviserMortgagePermissionSerializer

    def get_organisation(self):
        organisation = self.request.user.get_organisation()

        if not organisation:
            raise NotFound("Organisation not found for the user.")

        return organisation

    def get_mortgage(self, organisation):
        return get_object_or_404(
            Mortgage,
            alias=self.kwargs["mortgage_alias"],
            organisation=organisation,
        )

    def get_mortgage_adviser(self, organisation):
        adviser = get_object_or_404(
            User,
            alias=self.kwargs["adviser_alias"],
        )

        is_mortgage_adviser = OrganisationUser.objects.filter(
            user=adviser,
            organisation=organisation,
            role=OrganisationRoleChoices.MORTGAGE_ADVISER,
        ).exists()

        if not is_mortgage_adviser:
            raise ValidationError(
                "The selected user is not a mortgage adviser in this organisation."
            )

        return adviser

    def get_object(self):
        organisation = self.get_organisation()
        mortgage = self.get_mortgage(organisation)
        adviser = self.get_mortgage_adviser(organisation)

        permission, _ = MortgageAdviserMortgagePermission.objects.get_or_create(
            mortgage_adviser=adviser,
            mortgage=mortgage,
            organisation=organisation,
        )

        return permission

    def update(self, request, *args, **kwargs):
        permission = self.get_object()

        serializer = self.get_serializer(
            permission,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class MortgageAdviserPropertyListView(ListAPIView):
    serializer_class = MortgageAdviserPropertySerializer
    permission_classes = [IsMortgageAdviser]
    filterset_fields = ["property_type", "status"]
    search_fields = ["property_name", "address"]

    def get_queryset(self):
        organisation = self.request.user.get_organisation()
        if not organisation:
            raise NotFound("Organisation not found for the user.")

        return Property.objects.filter(
            organisation=organisation,
            mortgage_adviser_permissions__mortgage_adviser=self.request.user,
            mortgage_adviser_permissions__can_view=True,
        ).distinct()


class MortgageAdviserPropertyDetailView(RetrieveUpdateAPIView):
    serializer_class = MortgageAdviserPropertySerializer
    permission_classes = [IsMortgageAdviser, CanAccessMortgageAdviserProperty]

    def get_object(self):
        return get_object_or_404(
            Property,
            alias=self.kwargs["property_alias"],
            mortgage_adviser_permissions__mortgage_adviser=self.request.user,
            mortgage_adviser_permissions__can_view=True,
        )


class MortgageAdviserMortgageListView(ListAPIView):
    serializer_class = MortgageAdviserMortgageSerializers
    permission_classes = [IsMortgageAdviser]
    search_fields = [
        "property__property_name",
        "lender_name",
    ]

    def get_queryset(self):
        organisation = self.request.user.get_organisation()

        if not organisation:
            raise NotFound("Organisation not found for the user.")

        return Mortgage.objects.filter(
            organisation=organisation,
            mortgage_adviser_permissions__mortgage_adviser=self.request.user,
            mortgage_adviser_permissions__can_view=True,
        ).distinct()


class MortgageAdviserMortgageDetailView(RetrieveUpdateAPIView):
    serializer_class = MortgageAdviserMortgageSerializers
    permission_classes = [IsMortgageAdviser, CanAccessMortgageAdviserMortgage]

    def get_object(self):
        organisation = self.request.user.get_organisation()
        if not organisation:
            raise NotFound("Organisation not found for the user.")
        return get_object_or_404(
            Mortgage,
            alias=self.kwargs["mortgage_alias"],
            organisation=organisation,
            mortgage_adviser_permissions__mortgage_adviser=self.request.user,
            mortgage_adviser_permissions__can_view=True,
        )
