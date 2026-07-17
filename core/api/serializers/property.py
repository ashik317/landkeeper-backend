import os
from rest_framework import serializers
from apps.property.models import (
    Property,
    Mortgage,
    Tenant,
    ComplianceAndCertification,
    UploadDocument,
    Finance,
)
from common.models import Media, DocumentFile
from common.serializers import PropertySlimSerializer
from django.db import transaction


class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = [
            "id",
            "image",
            "description",
        ]


class DocumentFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentFile
        fields = ["id", "file", "description"]


class PropertySerializer(serializers.ModelSerializer):
    documents_data = serializers.ListField(
        child=serializers.ImageField(), required=False, write_only=True
    )
    documents = MediaSerializer(many=True, read_only=True)

    class Meta:
        model = Property
        fields = [
            "id",
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
            "rent_per_month",
            "notes",
            "documents",
            "documents_data",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "alias",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        documents_data = validated_data.pop("documents_data", [])

        property_obj = Property.objects.create(**validated_data)

        documents = [
            Media.objects.create(image=document) for document in documents_data
        ]

        property_obj.documents.set(documents)

        return property_obj

    def update(self, instance, validated_data):
        documents_data = validated_data.pop("documents_data", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if documents_data is not None:
            instance.documents.all().delete()

            documents = [
                Media.objects.create(image=document) for document in documents_data
            ]

            instance.documents.set(documents)

        return instance


class MortgageSerializers(serializers.ModelSerializer):
    mortgage_documents = serializers.ListField(
        child=serializers.FileField(), write_only=True, required=False
    )
    uploaded_documents = DocumentFileSerializer(
        source="mortgage_documents", many=True, read_only=True
    )

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

    def create(self, validated_data):
        uploaded_files = validated_data.pop("mortgage_documents", [])
        self._validate_mortgage_files(uploaded_files)
        mortgage = Mortgage.objects.create(**validated_data)

        for file in uploaded_files:
            doc_file = DocumentFile.objects.create(file=file)
            mortgage.mortgage_documents.add(doc_file)
        return mortgage

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


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = [
            "alias",
            "avatar",
            "title",
            "first_name",
            "middle_name",
            "last_name",
            "email",
            "phone",
            "image",
            "rent_amount",
            "deposit",
            "tenancy_start_date",
            "tenancy_end_date",
            "employment_details",
            "guarantor_name",
            "notes",
            "is_active",
            "property",
        ]
        read_only_fields = [
            "alias",
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["property"] = PropertySlimSerializer(instance.property).data
        return representation


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

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["property"] = PropertySlimSerializer(instance.property).data
        return representation


class UploadDocumentSerializer(serializers.ModelSerializer):
    files = DocumentFileSerializer(many=True, read_only=True)
    uploaded_files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = UploadDocument
        fields = [
            "alias",
            "property",
            "document_category",
            "document_name",
            "tags",
            "files",
            "uploaded_files",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["alias", "created_at", "updated_at"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["property"] = PropertySlimSerializer(instance.property).data
        return representation

    def _validate_files(self, files):
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

    def create(self, validated_data):
        uploaded_files = validated_data.pop("uploaded_files", [])
        self._validate_files(uploaded_files)
        upload_document = UploadDocument.objects.create(**validated_data)

        for file in uploaded_files:
            doc_file = DocumentFile.objects.create(file=file)
            upload_document.files.add(doc_file)
        return upload_document

    def update(self, instance, validated_data):
        uploaded_files = validated_data.pop("uploaded_files", None)

        if uploaded_files is not None:
            self._validate_files(uploaded_files)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if uploaded_files is not None:
            instance.files.all().delete()

            for file in uploaded_files:
                doc_file = DocumentFile.objects.create(file=file)
                instance.files.add(doc_file)

        return instance


class FinanceSerializer(serializers.ModelSerializer):
    receipt_files = DocumentFileSerializer(many=True, read_only=True, source="receipt")
    uploaded_receipt = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = Finance
        fields = [
            "alias",
            "property",
            "type",
            "category",
            "amount",
            "date",
            "description",
            "receipt_files",
            "uploaded_receipt",
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

    def validate_uploaded_receipt(self, receipt):
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

        for file in receipt:
            if file.size > limit:
                raise serializers.ValidationError(f"{file.name} exceeds 50MB limit.")
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in allowed_extensions:
                raise serializers.ValidationError(
                    f"{file.name} has an unsupported file type."
                )

        return receipt

    def create(self, validated_data):
        uploaded_receipt = validated_data.pop("uploaded_receipt", [])
        finance = Finance.objects.create(**validated_data)

        for file in uploaded_receipt:
            doc_file = DocumentFile.objects.create(file=file)
            finance.receipt.add(doc_file)
        return finance

    def update(self, instance, validated_data):
        uploaded_receipt = validated_data.pop("uploaded_receipt", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if uploaded_receipt is not None:
            # Delete old DocumentFile objects
            instance.receipt.all().delete()

            # Add new files
            for file in uploaded_receipt:
                doc_file = DocumentFile.objects.create(file=file)
                instance.receipt.add(doc_file)

        return instance

class PropertyOnboardingSerializer(serializers.Serializer):
    STEP_ORDER = ["property", "mortgage", "tenant", "compliance", "upload_document"]

    STEP_SERIALIZERS = {
        "property": PropertySerializer,
        "mortgage": MortgageSerializers,
        "tenant": TenantSerializer,
        "compliance": ComplianceAndCertificationSerializers,
        "upload_document": UploadDocumentSerializer,
    }

    property = serializers.DictField(required=False)
    mortgage = serializers.DictField(required=False)
    tenant = serializers.DictField(required=False)
    compliance = serializers.DictField(required=False)
    upload_document = serializers.DictField(required=False)

    def to_internal_value(self, data):
        if any(isinstance(data.get(step), dict) for step in self.STEP_ORDER if hasattr(data, "get")):
            return super().to_internal_value(data)

        nested = {}
        keys = data.keys() if hasattr(data, "keys") else []

        for key in keys:
            for step in self.STEP_ORDER:
                prefix = f"{step}_"
                if key.startswith(prefix):
                    field_name = key[len(prefix):]

                    if hasattr(data, "getlist"):
                        values = data.getlist(key)
                        value = values if len(values) > 1 else values[0]
                    else:
                        value = data.get(key)

                    nested.setdefault(step, {})[field_name] = value
                    break

        if nested:
            self.initial_data = nested
            return super().to_internal_value(nested)

        return super().to_internal_value(data)

    def validate(self, attrs):
        if not any(key in self.initial_data for key in self.STEP_ORDER):
            raise serializers.ValidationError(
                {"non_field_errors": ["At least one of property/mortgage/tenant/compliance/upload_document is required."]}
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]

        organisation_user = request.user.organisation_users.select_related(
            "organisation"
        ).first()

        if not organisation_user:
            raise serializers.ValidationError(
                {"organisation": ["User is not linked to any organisation."]}
            )

        organisation = organisation_user.organisation
        property_obj = None
        results = {}

        for step_name in self.STEP_ORDER:
            if step_name not in validated_data:
                continue

            serializer_class = self.STEP_SERIALIZERS[step_name]
            payload = dict(validated_data[step_name])

            if step_name != "property":
                if property_obj is None:
                    raise serializers.ValidationError(
                        {"property": ["Property must be created first in this batch."]}
                    )
                payload["property"] = property_obj.pk

            serializer = serializer_class(data=payload, context=self.context)
            serializer.is_valid(raise_exception=True)

            instance = serializer.save(organisation=organisation)

            if step_name == "property":
                property_obj = instance

            results[step_name] = serializer_class(instance, context=self.context).data

        return results