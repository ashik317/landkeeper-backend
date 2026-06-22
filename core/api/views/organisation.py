from rest_framework.exceptions import NotFound
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from apps.organisation.models import Organisation
from api.serializers.organisation import OrganisationSerializer


class OrganisationDetailView(RetrieveUpdateAPIView):
    serializer_class = OrganisationSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        try:
            return Organisation.objects.get(
                organisation_users__user=self.request.user,
                is_active=True,
            )
        except Organisation.DoesNotExist:
            raise NotFound("Organisation not found.")
