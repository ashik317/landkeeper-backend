from rest_framework.exceptions import NotFound
from rest_framework.generics import (
    RetrieveUpdateAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    ListAPIView
)
from rest_framework.permissions import IsAuthenticated
from apps.organisation.models import Organisation, OrganisationUser
from api.serializers.organisation import (
    OrganisationSerializer,
    OrganisationUserSerializer
)

class OrganisationListView(ListAPIView):
    serializer_class = OrganisationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Organisation.objects.filter(
            organisation_users__user=self.request.user,
            is_active=True,
        )

class OrganisationDetailView(RetrieveUpdateAPIView):
    serializer_class = OrganisationSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        try:
            return Organisation.objects.filter(
                slug=self.kwargs["organisation_slug"],
                organisation_users__user=self.request.user,
                is_active=True,
            ).distinct().get()
        except Organisation.DoesNotExist:
            raise NotFound("Organisation not found.")

class OrganisationUserListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrganisationUserSerializer

    def get_queryset(self):
        return OrganisationUser.objects.filter(
            organisation__slug=self.kwargs["organisation_slug"]
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["organisation"] = Organisation.objects.get(
            slug=self.kwargs["organisation_slug"]
        )
        return context


class OrganisationUserDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrganisationUserSerializer

    def get_queryset(self):
        return OrganisationUser.objects.filter(
            organisation__slug=self.kwargs["organisation_slug"],
            user__id=self.kwargs["pk"],
        )

    def get_object(self):
        try:
            return self.get_queryset().get()
        except OrganisationUser.DoesNotExist:
            raise NotFound("Organisation user not found.")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["organisation"] = Organisation.objects.get(
            slug=self.kwargs["organisation_slug"]
        )
        return context