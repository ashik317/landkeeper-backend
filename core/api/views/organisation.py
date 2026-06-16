from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView
)
from rest_framework.permissions import IsAuthenticated
from apps.organisation.models import Organisation
from api.serializers.organisation import OrganisationSerializer


class OrganisationOnboardingListAPIView(ListCreateAPIView):
    serializer_class = OrganisationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Organisation.objects.all()

class OrganisationOnboardingDetailAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = OrganisationSerializer
    permission_classes = [IsAuthenticated]
    queryset = Organisation.objects.all()
    lookup_field = "slug"
