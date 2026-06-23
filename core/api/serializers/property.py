from rest_framework import serializers
from apps.property.models import (
    Property,
    Mortgage,
    Tenant,
    ComplianceAndCertification,
)
from common.models import Media


class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = [
            "id",
            "image",
            "description",
        ]


class PropertySerializer(serializers.ModelSerializer):
    documents = MediaSerializer(many=True, required=False)

    class Meta:
        model = Property
        fields = [
            "alias",
            "property_name",
            "property_type",
            "status",
            "address",
            "purchase_price",
            "current_value",
            "purchase_date",
            "bedrooms",
            "bathrooms",
            "notes",
            "documents",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "alias",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        documents_data = validated_data.pop("documents", [])

        property_obj = Property.objects.create(**validated_data)

        for document_data in documents_data:
            media = Media.objects.create(**document_data)
            property_obj.documents.add(media)

        return property_obj

    def update(self, instance, validated_data):
        documents_data = validated_data.pop("documents", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if documents_data is not None:
            instance.documents.clear()
            for document_data in documents_data:
                media = Media.objects.create(**document_data)
                instance.documents.add(media)

        return instance


class MortgageSerializers(serializers.ModelSerializer):
    class Meta:
        model = Mortgage
        fields = [
            "alias",
            "property",
            "lender_name",
            "product_type",
            "interest_rate",
            "loan_amount",
            "outstanding_balance",
            "monthly_payment",
            "term",
            "start_date",
            "end_date",
            "broker_notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "alias",
            "created_at",
            "updated_at",
        ]


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = [
            "alias",
            "first_name",
            "last_name",
            "email",
            "phone",
            "rent_amount",
            "deposit",
            "tenancy_start_date",
            "tenancy_end_date",
            "employment_details",
            "guarantor_name",
            "notes",
            "property",
        ]
        read_only_fields = [
            "alias",
        ]


class ComplianceAndCertificationSerializers(serializers.ModelSerializer):
    class Meta:
        model = ComplianceAndCertification
        fields = [
            "alias",
            "property",
            "certificate_type",
            "issue_date",
            "expiry_date",
            "certificate_number",
            "issued_by",
            "certificate_file",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "alias",
            "created_at",
            "updated_at",
        ]
