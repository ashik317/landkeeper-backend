from django.db.models import Sum
from django.utils import timezone
from rest_framework import serializers
from apps.tenant.enums import RentPaymentStatusChoices
from apps.tenant.models import PaymentMethod, RentPayment

class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = [
            "alias",
            "tenant",
            "provider",
            "method_type",
            "provider_customer_id",
            "provider_mandate_id",
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
            "created_at",
            "updated_at"
        ]


class RentPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentPayment
        fields = [
            "alias",
            "tenant",
            "property",
            "organisation",
            "payment_method",
            "reference",
            "amount",
            "due_date",
            "paid_date",
            "status",
            "provider_payment_id",
            "receipt_file",
            "failure_reason",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "alias",
            "tenant",
            "property",
            "organisation",
            "reference",
            "created_at",
            "updated_at"
        ]


class RentBalanceSummarySerializer(serializers.Serializer):
    outstanding_balance = serializers.SerializerMethodField()
    next_due_date = serializers.SerializerMethodField()

    def get_outstanding_balance(self, tenant):
        total = RentPayment.objects.filter(tenant=tenant).exclude(
            status=RentPaymentStatusChoices.CLEARED
        ).aggregate(total=Sum("amount"))["total"]
        return total or 0

    def get_next_due_date(self, tenant):
        next_payment = (
            RentPayment.objects.filter(
                tenant=tenant, due_date__gte=timezone.localdate()
            )
            .exclude(status=RentPaymentStatusChoices.CLEARED)
            .order_by("due_date")
            .first()
        )
        return next_payment.due_date if next_payment else None

class DirectDebitSetupRequestSerializer(serializers.Serializer):
    success_redirect_url = serializers.URLField()


class DirectDebitCompleteRequestSerializer(serializers.Serializer):
    redirect_flow_id = serializers.CharField()
    session_token = serializers.CharField()

class CardPaymentRequestSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_method_id = serializers.CharField(required=False, allow_blank=True)