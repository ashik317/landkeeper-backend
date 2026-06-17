from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from apps.property.models import Property
from serializers.property import PropertySerializer


class PropertyListCreateAPIView(ListCreateAPIView):
    serializer_class = PropertySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Property.objects.all()

