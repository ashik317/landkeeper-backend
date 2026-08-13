import os

from rest_framework import serializers

from apps.property.models import (
    Property,
    PropertyOwnership,
    Media,
    Mortgage,
    DocumentFile,
    MortgageAdviserPropertyPermission,
    MortgageAdviserMortgagePermission,
)
from apps.organisation.enums import OrganisationRoleChoices
from apps.property.enums import PropertyOwnerType

from common.serializers import (
    MediaSlimSerializer,
    PropertySlimSerializer,
    DocumentFileSlimSerializer,
)

class MortgageAdviserPropertyPermissionSlimSerializer(serializers.ModelSerializer):
    property = serializers.UUIDField(source="property.alias", read_only=True)
    mortgage_adviser = serializers.UUIDField(
        source="mortgage_adviser.alias", read_only=True
    )

    class Meta:
        model = MortgageAdviserPropertyPermission
        fields = [
            "mortgage_adviser",
            "property",
            "can_view",
            "can_edit",
        ]

class MortgageAdviserMortgagePermissionSlimSerializer(serializers.ModelSerializer):
    mortgage = serializers.UUIDField(source="mortgage.alias", read_only=True)
    mortgage_adviser = serializers.UUIDField(
        source="mortgage_adviser.alias", read_only=True
    )

    class Meta:
        model = MortgageAdviserMortgagePermission
        fields = [
            "mortgage_adviser",
            "mortgage",
            "can_view",
            "can_edit",
        ]

class MortgageAdviserPropertyPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MortgageAdviserPropertyPermission
        fields = [
            "can_view",
            "can_edit",
        ]


class MortgageAdviserMortgagePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MortgageAdviserMortgagePermission
        fields = [
            "can_view",
            "can_edit",
        ]


class PropertyOwnershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyOwnership
        fields = [
            "shareholder_name",
            "owner_name",
            "share_percentage",
        ]
        extra_kwargs = {
            "owner_name": {"required": False, "allow_null": True, "allow_blank": True},
            "shareholder_name": {
                "required": False,
                "allow_null": True,
                "allow_blank": True,
            },
            "share_percentage": {"required": False, "allow_null": True},
        }

    def to_representation(self, instance):
        rep = {}
        property_owner = getattr(instance.property, "property_owner", None)

        if property_owner == PropertyOwnerType.COMPANY:
            rep["shareholder_name"] = instance.shareholder_name
            rep["share_percentage"] = instance.share_percentage
        else:
            rep["owner_name"] = instance.owner_name

        return rep


class MortgageAdviserPropertySerializer(serializers.ModelSerializer):
    documents_data = serializers.ListField(
        child=serializers.ImageField(), required=False, write_only=True
    )
    documents = MediaSlimSerializer(many=True, read_only=True)
    shareholder = PropertyOwnershipSerializer(many=True, required=False)
    landlord = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            "id",
            "alias",
            "landlord",
            "property_name",
            "property_owner",
            "company_name",
            "property_type",
            "status",
            "address",
            "purchase_price",
            "current_value",
            "purchase_date",
            "year_built",
            "property_tenure",
            "remaining_lease_term",
            "monthly_service_charge",
            "annual_ground_rent",
            "bedrooms",
            "bathrooms",
            "council_tax_band",
            "local_authority",
            "monthly_rental_income",
            "notes",
            "shareholder",
            "documents",
            "documents_data",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "alias",
            "landlord",
            "created_at",
            "updated_at",
        ]

    def get_landlord(self, obj):
        organisation_user = (
            obj.organisation.organisation_users.select_related("user")
            .filter(role=OrganisationRoleChoices.LANDLORD)
            .first()
        )
        if organisation_user is None:
            return None

        user = organisation_user.user
        return {
            "id": user.id,
            "full_name": user.get_full_name(),
            "email": user.email,
            "phone": user.phone,
            "profile_image": user.profile_image.url if user.profile_image else None,
            "current_address": user.current_address,
            "ni_number": user.ni_number,
            "utr_number": user.utr_number,
        }

    def validate(self, attrs):
        property_owner = attrs.get(
            "property_owner",
            getattr(self.instance, "property_owner", None),
        )
        shareholder = attrs.get("shareholder")

        if shareholder:
            if property_owner == PropertyOwnerType.COMPANY:
                for owner in shareholder:
                    if owner.get("share_percentage") in (None, ""):
                        raise serializers.ValidationError(
                            {
                                "shareholder": [
                                    "share_percentage is required when property_owner is COMPANY."
                                ]
                            }
                        )
                    owner["owner_name"] = None
            elif property_owner == PropertyOwnerType.OWNER:
                for owner in shareholder:
                    owner["share_percentage"] = None
                    owner["shareholder_name"] = None

        return attrs

    MULTI_VALUE_FIELDS = {"documents_data"}

    def to_internal_value(self, data):
        if hasattr(data, "getlist"):
            plain_data = {}
            for key in data.keys():
                values = data.getlist(key)
                if key in self.MULTI_VALUE_FIELDS:
                    plain_data[key] = values
                else:
                    plain_data[key] = values if len(values) > 1 else values[0]
        else:
            plain_data = dict(data)

        shareholder = []
        index = 0
        while True:
            owner_name_key = f"shareholder[{index}].owner_name"
            shareholder_name_key = f"shareholder[{index}].shareholder_name"
            share_percentage_key = f"shareholder[{index}].share_percentage"

            if (
                owner_name_key not in plain_data
                and shareholder_name_key not in plain_data
                and share_percentage_key not in plain_data
            ):
                break

            shareholder.append(
                {
                    "owner_name": plain_data.pop(owner_name_key, None),
                    "shareholder_name": plain_data.pop(shareholder_name_key, None),
                    "share_percentage": plain_data.pop(share_percentage_key, None),
                }
            )
            index += 1

        if shareholder:
            plain_data["shareholder"] = shareholder
        elif "shareholder" not in plain_data:
            plain_data["shareholder"] = []

        return super().to_internal_value(plain_data)

    def update(self, instance, validated_data):
        documents_data = validated_data.pop("documents_data", None)
        shareholder = validated_data.pop("shareholder", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if documents_data is not None:
            instance.documents.all().delete()
            documents = [Media.objects.create(image=d) for d in documents_data]
            instance.documents.set(documents)

        if shareholder is not None:
            instance.shareholder.all().delete()
            for owner in shareholder:
                PropertyOwnership.objects.create(property=instance, **owner)

        return instance


class MortgageAdviserMortgageSerializers(serializers.ModelSerializer):
    mortgage_documents = serializers.ListField(
        child=serializers.FileField(), write_only=True, required=False
    )
    uploaded_documents = DocumentFileSlimSerializer(
        source="mortgage_documents", many=True, read_only=True
    )

    class Meta:
        model = Mortgage
        fields = [
            "alias",
            "property",
            "lender_name",
            "interest_rate_type",
            "interest_rate",
            "interest_rate_expiry_date",
            "outstanding_balance",
            "monthly_payment",
            "remaining_mortgage",
            "epc_rating",
            "epc_certificate_expiry_date",
            "notes",
            "mortgage_documents",
            "uploaded_documents",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "alias",
            "created_at",
            "updated_at",
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["property"] = PropertySlimSerializer(instance.property).data
        return representation

    def _validate_mortgage_files(self, files):
        allowed_extensions = [
            ".pdf",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".jpg",
            ".jpeg",
            ".png",
        ]
        limit = 50 * 1024 * 1024
        for file in files:
            if file.size > limit:
                raise serializers.ValidationError(f"{file.name} exceeds 50MB limit.")
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in allowed_extensions:
                raise serializers.ValidationError(
                    f"{file.name} has an unsupported file type."
                )

    def update(self, instance, validated_data):
        uploaded_files = validated_data.pop("mortgage_documents", None)

        if uploaded_files is not None:
            self._validate_mortgage_files(uploaded_files)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if uploaded_files is not None:
            instance.mortgage_documents.all().delete()

            for file in uploaded_files:
                doc_file = DocumentFile.objects.create(file=file)
                instance.mortgage_documents.add(doc_file)

        return instance
