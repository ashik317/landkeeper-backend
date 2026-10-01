from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import (
    ListAPIView,
    RetrieveUpdateDestroyAPIView,
    ListCreateAPIView
)
from api.serializers.admin import LandloardSerializer
from api.serializers.property import PropertySerializer
from apps.organisation.enums import OrganisationRoleChoices
from apps.organisation.models import OrganisationUser
from apps.property.models import Property
from common.permission import IsSuperAdmin

User = get_user_model()


class LandloardView(ListAPIView):
    permission_classes = [IsSuperAdmin]
    serializer_class = LandloardSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter]

    filterset_fields = {
        "is_active": ["exact"],
        "organisation_users__organisation__subscription__status": ["exact"],
        "organisation_users__organisation__subscription__plan__plan_type": ["exact"],
        "created_at": ["gte", "lte"],
    }

    search_fields = [
        "email",
        "title",
        "first_name",
        "middle_name",
        "last_name",
        "current_address",
        "ni_number",
        "utr_number",
        "phone",
    ]

    def get_queryset(self):
        return (
            User.objects
            .filter(
                organisation_users__role=OrganisationRoleChoices.LANDLORD
            )
            .distinct()
        )


class LandloardDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSuperAdmin]
    serializer_class = LandloardSerializer

    def get_object(self):
        return get_object_or_404(
            User,
            alias=self.kwargs["landloard_alias"],
            organisation_users__role=OrganisationRoleChoices.LANDLORD,
        )

    def perform_destroy(self, instance):
        instance.delete()


class SuperAdminLandlordPropertyView(ListCreateAPIView):
    serializer_class = PropertySerializer
    permission_classes = [IsSuperAdmin]
    filterset_fields = ["property_type", "status"]
    search_fields = ["property_name", "address"]

    def get_landlord(self):
        return get_object_or_404(
            OrganisationUser,
            user__alias=self.kwargs["landlord_alias"],
            role=OrganisationRoleChoices.LANDLORD,
        )

    def get_queryset(self):
        landlord = self.get_landlord()
        return Property.objects.filter(organisation=landlord.organisation)

    def perform_create(self, serializer):
        landlord = self.get_landlord()
        serializer.save(organisation=landlord.organisation)


class SuperAdminLandlordPropertyDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = PropertySerializer
    permission_classes = [IsSuperAdmin]

    def get_object(self):
        landlord = get_object_or_404(
            OrganisationUser,
            user__alias=self.kwargs["landlord_alias"],
            role=OrganisationRoleChoices.LANDLORD,
        )
        return get_object_or_404(
            Property,
            alias=self.kwargs["property_alias"],
            organisation=landlord.organisation,
        )