import logging
from datetime import date

import stripe
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework import serializers

from apps.organisation.enums import OrganisationRoleChoices
from apps.organisation.models import OrganisationUser
from apps.property.models import Tenant
from apps.tenant.enums import (
    RentPaymentStatusChoices,
)
from apps.tenant.models import (
    PaymentMethod,
    CardPayment,
    MaintenanceRequest,
    MaintenanceRequestComment,
)
from common.models import DocumentFile
from common.serializers import TenantSlimSerializer

logger = logging.getLogger(__name__)


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = [
            "alias",
            "tenant",
            "organisation",
            "provider",
            "method_type",
            "provider_customer_id",
            "provider_payment_method_id",
            "status",
            "is_default",
            "card_last4",
            "card_brand",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "alias",
            "tenant",
            "organisation",
            "provider",
            "provider_customer_id",
            "provider_payment_method_id",
            "status",
            "is_default",
            "card_last4",
            "card_brand",
            "created_at",
            "updated_at",
        ]


class PaymentHistorySerializer(serializers.ModelSerializer):
    status = serializers.CharField(source="get_status_display")
    card = serializers.SerializerMethodField()
    invoice_url = serializers.SerializerMethodField()

    class Meta:
        model = CardPayment
        fields = [
            "alias",
            "amount",
            "due_date",
            "status",
            "failure_reason",
            "provider_payment_id",
            "card",
            "invoice_url",
            "note",
            "created_at",
            "updated_at",
        ]

    def get_card(self, obj):
        payment_method = obj.payment_method

        if not payment_method:
            return None

        return {
            "provider": payment_method.provider,
            "method_type": payment_method.method_type,
            "card_last4": payment_method.card_last4,
            "card_brand": payment_method.card_brand,
            "card_exp_month": payment_method.card_exp_month,
            "card_exp_year": payment_method.card_exp_year,
        }

    def get_invoice_url(self, obj):
        if not obj.provider_payment_id or obj.get_status_display() != "Cleared":
            return None

        try:
            intent = stripe.PaymentIntent.retrieve(
                obj.provider_payment_id,
                expand=["latest_charge"],
            )

            charge = intent.latest_charge

            return charge.receipt_url if charge else None

        except stripe.error.StripeError:
            logger.exception(
                "PaymentHistoryView: failed to fetch invoice/receipt URL",
                extra={
                    "provider_payment_id": obj.provider_payment_id,
                },
            )
            return None


class RentBalanceSummarySerializer(serializers.Serializer):
    current_rent_amount = serializers.SerializerMethodField()
    outstanding_balance = serializers.SerializerMethodField()
    next_due_date = serializers.SerializerMethodField()

    def get_current_rent_amount(self, tenant):
        return tenant.rent_amount or 0

    def _get_total_paid_this_month(self, tenant):
        today = timezone.localdate()
        month_start = today.replace(day=1)

        total = CardPayment.objects.filter(
            tenant=tenant,
            status=RentPaymentStatusChoices.CLEARED,
            due_date__gte=month_start,
        ).aggregate(total=Sum("amount"))["total"]
        return total or 0

    def get_outstanding_balance(self, tenant):
        rent_amount = tenant.rent_amount or 0
        total_paid = self._get_total_paid_this_month(tenant)

        if total_paid == 0:
            return rent_amount

        return rent_amount - total_paid

    def get_next_due_date(self, tenant):
        today = timezone.localdate()
        month_start = today.replace(day=1)
        total_paid = self._get_total_paid_this_month(tenant)

        if total_paid > 0:
            year, month = month_start.year, month_start.month
            month += 1
            if month > 12:
                month = 1
                year += 1
            return date(year, month, 1)

        return month_start


class CardPaymentRequestSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    payment_method_id = serializers.CharField(required=False, allow_blank=True)
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class CardPaymentSerializer(serializers.ModelSerializer):
    payment_method = PaymentMethodSerializer(read_only=True)

    class Meta:
        model = CardPayment
        fields = [
            "alias",
            "payment_method",
            "amount",
            "due_date",
            "status",
            "provider_payment_id",
            "failure_reason",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class DocumentFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentFile
        fields = ["id", "file"]


class MaintenanceRequestSerializer(serializers.ModelSerializer):
    documents = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        write_only=True,
    )
    removed_document_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
    )

    request_id = serializers.SerializerMethodField()
    tenant = TenantSlimSerializer(read_only=True)
    property = serializers.SerializerMethodField()
    organisation = serializers.SerializerMethodField()

    class Meta:
        model = MaintenanceRequest
        fields = [
            "alias",
            "request_id",
            "tenant",
            "property",
            "organisation",
            "issue",
            "category",
            "current_status",
            "is_emergency",
            "notes",
            "documents",
            "removed_document_ids",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "alias",
            "tenant",
            "property",
            "organisation",
            "created_at",
            "updated_at",
        ]

    def get_request_id(self, obj):
        return f"MR-{obj.id:08d}"

    def get_property(self, obj):
        if not obj.property:
            return None
        return f"{obj.property.property_name} - {obj.property.address}"

    def get_organisation(self, obj):
        return obj.organisation.name if obj.organisation else None

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["documents"] = DocumentFileSerializer(
            instance.documents.all(), many=True, context=self.context
        ).data
        return rep

    def validate(self, attrs):
        user = self.context["request"].user

        if isinstance(user, Tenant):
            attrs.pop("current_status", None)
            return attrs

        is_landlord = OrganisationUser.objects.filter(
            user=user,
            role=OrganisationRoleChoices.LANDLORD,
        ).exists()

        if is_landlord:
            allowed_fields = {"current_status"}
            invalid_fields = set(attrs.keys()) - allowed_fields
            if invalid_fields:
                raise serializers.ValidationError(
                    {
                        "detail": "Landlords can only update the maintenance request status."
                    }
                )
        return attrs

    def create(self, validated_data):
        new_files = validated_data.pop("documents", [])
        instance = super().create(validated_data)
        for f in new_files:
            doc = DocumentFile.objects.create(file=f)
            instance.documents.add(doc)
        return instance

    def update(self, instance, validated_data):
        for field in ("tenant", "property", "organisation"):
            validated_data.pop(field, None)

        new_files = validated_data.pop("documents", [])
        removed_ids = validated_data.pop("removed_document_ids", [])

        with transaction.atomic():
            instance = super().update(instance, validated_data)

            if removed_ids:
                docs_to_remove = instance.documents.filter(id__in=removed_ids)
                instance.documents.remove(*docs_to_remove)
                docs_to_remove.delete()

            for f in new_files:
                doc = DocumentFile.objects.create(file=f)
                instance.documents.add(doc)

        return instance


class MaintenanceRequestCommentAuthorSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.SerializerMethodField()
    email = serializers.EmailField()
    type = serializers.SerializerMethodField()

    def get_name(self, obj):
        return obj.get_full_name()

    def get_type(self, obj):
        return "tenant" if isinstance(obj, Tenant) else "staff"


class MaintenanceRequestCommentSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    documents = DocumentFileSerializer(many=True, read_only=True)
    upload_files = serializers.ListField(
        child=serializers.FileField(), write_only=True, required=False
    )

    class Meta:
        model = MaintenanceRequestComment
        fields = [
            "id",
            "alias",
            "message",
            "parent",
            "author",
            "documents",
            "upload_files",
            "replies",
            "created_at",
        ]
        read_only_fields = ["id", "alias", "author", "created_at"]

    def get_author(self, obj):
        return MaintenanceRequestCommentAuthorSerializer(obj.author).data

    def get_replies(self, obj):
        replies = obj.replies.all().order_by("created_at")
        return MaintenanceRequestCommentSerializer(
            replies, many=True, context=self.context
        ).data

    def validate(self, attrs):
        parent = attrs.get("parent")
        maintenance_request = self.context.get("maintenance_request")
        if (
            parent
            and maintenance_request
            and parent.maintenance_request_id != maintenance_request.id
        ):
            raise serializers.ValidationError(
                {
                    "parent": "Parent comment must belong to the same maintenance request."
                }
            )
        return attrs

    def create(self, validated_data):
        upload_files = validated_data.pop("upload_files", [])
        comment = MaintenanceRequestComment.objects.create(**validated_data)
        documents = [DocumentFile.objects.create(file=f) for f in upload_files]
        if documents:
            comment.documents.add(*documents)
        return comment

    def update(self, instance, validated_data):
        upload_files = validated_data.pop("upload_files", [])
        instance = super().update(instance, validated_data)
        if upload_files:
            for old_document in instance.documents.all():
                instance.documents.remove(old_document)
                old_document.file.delete(save=False)
                old_document.delete()
            new_documents = [DocumentFile.objects.create(file=f) for f in upload_files]
            instance.documents.add(*new_documents)
        return instance


class LandlordCardPaymentSerializer(serializers.ModelSerializer):
    tenant_id = serializers.IntegerField(source="tenant.id", read_only=True)
    tenant_name = serializers.SerializerMethodField()
    tenant_alias = serializers.UUIDField(source="tenant.alias", read_only=True)
    property_name = serializers.CharField(
        source="tenant.property.property_name", read_only=True
    )
    property_address = serializers.CharField(
        source="tenant.property.address", read_only=True
    )
    card_last4 = serializers.SerializerMethodField()
    card_brand = serializers.SerializerMethodField()
    invoice_url = serializers.SerializerMethodField()

    class Meta:
        model = CardPayment
        fields = [
            "alias",
            "tenant_id",
            "tenant_name",
            "tenant_alias",
            "property_name",
            "property_address",
            "amount",
            "due_date",
            "status",
            "failure_reason",
            "provider_payment_id",
            "card_last4",
            "card_brand",
            "invoice_url",
            "note",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_tenant_name(self, obj):
        return obj.tenant.get_full_name()

    def get_card_last4(self, obj):
        return obj.payment_method.card_last4 if obj.payment_method else None

    def get_card_brand(self, obj):
        return obj.payment_method.card_brand if obj.payment_method else None

    def get_invoice_url(self, obj):
        if not obj.provider_payment_id:
            return None
        try:
            intent = stripe.PaymentIntent.retrieve(
                obj.provider_payment_id, expand=["latest_charge"]
            )
            charge = intent.latest_charge
            return charge.receipt_url if charge else None
        except stripe.error.StripeError:
            return None
