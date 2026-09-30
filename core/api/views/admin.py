from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView
from api.serializers.admin import LandloardProfileSerializer
from apps.organisation.enums import OrganisationRoleChoices
from common.permission import IsSuperAdmin

User = get_user_model()


class LandloardProfileView(ListAPIView):
    permission_classes = [IsSuperAdmin]
    serializer_class = LandloardProfileSerializer

    def get_queryset(self):
        return (
            User.objects
            .filter(
                organisation_users__role=OrganisationRoleChoices.LANDLORD
            )
            .distinct()
        )


class LandloardProfileDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSuperAdmin]
    serializer_class = LandloardProfileSerializer

    def get_object(self):
        return get_object_or_404(
            User,
            alias=self.kwargs["landloard_alias"],
            organisation_users__role=OrganisationRoleChoices.LANDLORD,
        )

    def perform_destroy(self, instance):
        instance.delete()