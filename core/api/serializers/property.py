import os
from rest_framework import serializers
from apps.property.models import (
    Property,
    Mortgage,
    Tenant,
    ComplianceAndCertification,
    UploadDocument,
)
from common.models import (
    Media,
    DocumentFile
)


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

class DocumentFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentFile
        fields = [
            "id",
            "file",
            "description"
        ]


class UploadDocumentSerializer(serializers.ModelSerializer):
    files = DocumentFileSerializer(many=True, read_only=True)
    uploaded_files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False,
    )
    property_name = serializers.CharField(source="property.property_name", read_only=True)

    class Meta:
        model = UploadDocument
        fields = [
            "alias",
            "property",
            "property_name",
            "document_category",
            "document_name",
            "tags",
            "files",
            "uploaded_files",
        ]

    def validate_uploaded_files(self, files):
        allowed_extensions = [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".jpg", ".jpeg", ".png"]
        limit = 50 * 1024 * 1024  # 50MB

        for file in files:
            if file.size > limit:
                raise serializers.ValidationError(f"{file.name} exceeds 50MB limit.")
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in allowed_extensions:
                raise serializers.ValidationError(f"{file.name} has an unsupported file type.")

        return files

    def create(self, validated_data):
        uploaded_files = validated_data.pop("uploaded_files", [])
        upload_document = UploadDocument.objects.create(**validated_data)

        for file in uploaded_files:
            doc_file = DocumentFile.objects.create(file=file)
            upload_document.files.add(doc_file)

        return upload_document

    def update(self, instance, validated_data):
        uploaded_files = validated_data.pop("uploaded_files", [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        for file in uploaded_files:
            doc_file = DocumentFile.objects.create(file=file)
            instance.files.add(doc_file)

        return instance