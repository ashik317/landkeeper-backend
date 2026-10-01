import logging
from datetime import date
from decimal import Decimal

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
    invoice_url = serializers.URLField(read_only=True)

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

class RentBalanceSummarySerializer(serializers.Serializer):
    current_rent_amount = serializers.SerializerMethodField()
    total_paid = serializers.SerializerMethodField()
    outstanding_balance = serializers.SerializerMethodField()
    credit_balance = serializers.SerializerMethodField()
    next_due_date = serializers.SerializerMethodField()

    @staticmethod
    def _add_months(d, n):
        """Return the 1st day of the month that is n months after d."""
        total = d.year * 12 + (d.month - 1) + n
        return date(total // 12, total % 12 + 1, 1)

    @staticmethod
    def _months_between(start, end):
        """Number of months from start's month to end's month, inclusive."""
        return (end.year - start.year) * 12 + (end.month - start.month) + 1

    @staticmethod
    def _get_start_month(tenant, today):
        """Billing starts from the month of the tenant's first payment."""
        first_due = (
            CardPayment.objects.filter(tenant=tenant)
            .order_by("due_date")
            .values_list("due_date", flat=True)
            .first()
        )
        return (first_due or today).replace(day=1)


    def _summary(self, tenant):
        cache = self.__dict__.setdefault("_summary_cache", {})
        if tenant.pk in cache:
            return cache[tenant.pk]

        today = timezone.localdate()
        rent = Decimal(tenant.rent_amount or 0)
        start = self._get_start_month(tenant, today)

        months_billed = max(self._months_between(start, today), 0)
        total_charged = rent * months_billed

        total_paid = CardPayment.objects.filter(
            tenant=tenant,
            status=RentPaymentStatusChoices.CLEARED,
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

        balance = total_charged - total_paid

        if rent > 0:
            months_covered = int(total_paid // rent)
            next_due = self._add_months(start, months_covered)
        else:
            next_due = None

        result = {
            "rent": rent,
            "total_paid": total_paid,
            "outstanding": max(balance, Decimal("0")),
            "credit": max(-balance, Decimal("0")),
            "next_due": next_due,
        }
        cache[tenant.pk] = result
        return result


    def get_current_rent_amount(self, tenant):
        return self._summary(tenant)["rent"]

    def get_total_paid(self, tenant):
        return self._summary(tenant)["total_paid"]

    def get_outstanding_balance(self, tenant):
        return self._summary(tenant)["outstanding"]

    def get_credit_balance(self, tenant):
        return self._summary(tenant)["credit"]

    def get_next_due_date(self, tenant):
        return self._summary(tenant)["next_due"]


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
        source="tenant.property.property_name",
        read_only=True,
    )

    property_address = serializers.CharField(
        source="tenant.property.address",
        read_only=True,
    )

    card_last4 = serializers.SerializerMethodField()
    card_brand = serializers.SerializerMethodField()

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
