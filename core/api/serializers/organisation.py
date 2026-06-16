from rest_framework import serializers
from apps.organisation.models import Organisation


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
            "contact_person_designation",
            "website",
            "address",
            "is_active",
            "is_approved",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "slug",
            "is_active",
            "is_approved",
            "created_at",
            "updated_at",
        ]