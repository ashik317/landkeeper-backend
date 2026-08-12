from django.shortcuts import get_object_or_404

from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView
from rest_framework.exceptions import NotFound

from apps.property.models import Property, Mortgage

from ..serializers.mortgage_advisers import (
    MortgageAdviserPropertySerializer,
    MortgageAdviserMortgageSerializers,
)

from common.permission import IsMortgageAdviser


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
            organisation=organisation, is_visible_mortgage_adviser=True
        )


class MortgageAdviserPropertyDetailView(RetrieveUpdateAPIView):
    serializer_class = MortgageAdviserPropertySerializer
    permission_classes = [IsMortgageAdviser]

    def get_object(self):
        return get_object_or_404(
            Property,
            alias=self.kwargs["property_alias"],
            is_visible_mortgage_adviser=True,
        )


class MortgageAdviserMortgageListView(ListAPIView):
    serializer_class = MortgageAdviserMortgageSerializers
    permission_classes = [IsMortgageAdviser]
    search_fields = ["property__property_name", "lender_name"]

    def get_queryset(self):
        organisation = self.request.user.get_organisation()
        if not organisation:
            raise NotFound("Organisation not found for the user.")
        return Mortgage.objects.filter(
            organisation=organisation, is_visible_mortgage_adviser=True
        )


class MortgageAdviserMortgageDetailView(RetrieveUpdateAPIView):
    serializer_class = MortgageAdviserMortgageSerializers
    permission_classes = [IsMortgageAdviser]

    def get_object(self):
        organisation = self.request.user.get_organisation()
        if not organisation:
            raise NotFound("Organisation not found for the user.")
        return get_object_or_404(
            Mortgage,
            alias=self.kwargs["mortgage_alias"],
            organisation=organisation,
            is_visible_mortgage_adviser=True,
        )
