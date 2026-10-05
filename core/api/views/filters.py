from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from apps.property.models import Property
from apps.organisation.utils import get_request_organisation

from ..serializers.filters import PropertyFilterSerializer


class PropertyFilterListView(ListAPIView):
    serializer_class = PropertyFilterSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["property_name"]
    pagination_class = None

    def get_queryset(self):
        organisation = get_request_organisation(self.request)

        return Property.objects.filter(organisation=organisation)
