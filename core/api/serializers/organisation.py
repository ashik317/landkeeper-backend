from rest_framework import serializers
from apps.organisation.models import Organisation, OrganisationUser


class OrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = [
            "slug",
            "name",
            "description",
            "email",
            "logo",
            "profile_image",
            "primary_mobile",
            "other_contact",
            "contact_person",
            "website",
            "address",
            "is_active",
            "created_at",
            "updated_at",
        ]
