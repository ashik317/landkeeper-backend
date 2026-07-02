from rest_framework import serializers

from apps.property.models import Property


class PropertySlimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = ["id", "alias", "property_name"]
