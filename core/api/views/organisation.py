from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound
from rest_framework.generics import (
    RetrieveUpdateAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    ListAPIView,
)
from rest_framework.permissions import IsAuthenticated

from apps.authentication.models import InviteUser
from apps.organisation.models import Organisation, OrganisationUser
from api.serializers.organisation import (
    OrganisationSerializer,
    OrganisationUserSerializer,
    OrganisationInviterUserSerializer,
)


class OrganisationDetailView(RetrieveUpdateAPIView):
    serializer_class = OrganisationSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        organisation = self.request.user.get_organisation()
        if not organisation:
            raise NotFound("Organisation not found.")
        return organisation


class OrganisationUserListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrganisationUserSerializer

    def get_queryset(self):
        organisation = self.request.user.get_organisation()
        if not organisation:
            raise NotFound("Organisation not found.")
        return OrganisationUser.objects.filter(organisation=organisation).exclude(
            role="LANDLORD"
        )


class OrganisationInviteUserView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrganisationInviterUserSerializer

    def get_queryset(self):
        organisation = self.request.user.get_organisation()
        if not organisation:
            raise NotFound("Organisation not found.")
        return InviteUser.objects.filter(organisation=organisation)


class OrganisationUserDetailView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrganisationUserSerializer

    def get_queryset(self):
        organisation = self.request.user.get_organisation()
        if not organisation:
            raise NotFound("Organisation not found.")
        return OrganisationUser.objects.filter(
            organisation=organisation,
            user__alias=self.kwargs["user_alias"],
        ).exclude(role="LANDLORD")

    def get_object(self):
        try:
            return self.get_queryset().get()
        except OrganisationUser.DoesNotExist:
            raise NotFound("Organisation user not found.")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["organisation"] = self.request.user.get_organisation()
        return context
