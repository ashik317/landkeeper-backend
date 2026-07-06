from rest_framework import serializers
from apps.authentication.models import InviteUser
from apps.organisation.models import Organisation, OrganisationUser, User


class OrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = [
            "slug",
            "name",
            "description",
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


class OrganisationUserMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "alias",
            "title",
            "first_name",
            "middle_name",
            "last_name",
            "email",
            "phone",
            "profile_image",
            "is_active",
        ]
        read_only_fields = ["alias", "email"]


class OrganisationUserSerializer(serializers.ModelSerializer):
    user = OrganisationUserMinimalSerializer()

    class Meta:
        model = OrganisationUser
        fields = [
            "user",
            "role",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
        ]

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", None)

        if user_data:
            user = instance.user
            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()

        return super().update(instance, validated_data)


class OrganisationInviterUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = InviteUser
        fields = [
            "alias",
            "email",
            "role",
            "message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
        ]
