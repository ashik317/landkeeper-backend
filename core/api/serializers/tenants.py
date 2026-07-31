from django.db.models import Sum
from django.utils import timezone
from rest_framework import serializers

from apps.tenant.enums import RentPaymentStatusChoices, PaymentProviderChoices
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
            "provider",
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


class RentPaymentSerializer(serializers.ModelSerializer):
    payment_method = PaymentMethodSerializer(read_only=True)

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
            "paid_date",
            "status",
            "provider_payment_id",
            "receipt_file",
            "failure_reason",
            "created_at",
            "updated_at",
        ]


class RentBalanceSummarySerializer(serializers.Serializer):
    current_rent_amount = serializers.SerializerMethodField()
    outstanding_balance = serializers.SerializerMethodField()
    next_due_date = serializers.SerializerMethodField()

    def get_current_rent_amount(self, tenant):
        latest_payment = (
            RentPayment.objects.filter(tenant=tenant)
            .order_by("-due_date")
            .first()
        )
        return latest_payment.amount if latest_payment else 0

    def get_outstanding_balance(self, tenant):
        total = (
            RentPayment.objects.filter(tenant=tenant)
            .exclude(
                status__in=[
                    RentPaymentStatusChoices.CLEARED,
                    RentPaymentStatusChoices.REFUNDED,
                ]
            )
            .aggregate(total=Sum("amount"))["total"]
        )
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
    _BLOCKED_FOR_NEW_ATTEMPT_STATUSES = (
        RentPaymentStatusChoices.CLEARED,
        RentPaymentStatusChoices.PROCESSING,
    )

    rent_payment = serializers.SlugRelatedField(
        slug_field="alias",
        queryset=RentPayment.objects.all(),
    )
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    payment_method_id = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        request = self.context["request"]
        rent_payment = attrs["rent_payment"]

        if rent_payment.tenant_id != request.user.id:
            raise serializers.ValidationError({"rent_payment": "Not found."})

        if rent_payment.status in self._BLOCKED_FOR_NEW_ATTEMPT_STATUSES:
            raise serializers.ValidationError(
                {"rent_payment": "This rent payment is already cleared or being processed."}
            )

        if attrs["amount"] != rent_payment.amount:
            raise serializers.ValidationError(
                {"amount": f"Amount must match the rent payment amount of £{rent_payment.amount}."}
            )
        return attrs


class DirectDebitPaymentRequestSerializer(serializers.Serializer):
    _BLOCKED_FOR_NEW_ATTEMPT_STATUSES = (
        RentPaymentStatusChoices.CLEARED,
        RentPaymentStatusChoices.PROCESSING,
    )

    rent_payment = serializers.SlugRelatedField(
        slug_field="alias",
        queryset=RentPayment.objects.all(),
    )

    def validate_rent_payment(self, rent_payment):
        request = self.context["request"]
        if rent_payment.tenant_id != request.user.id:
            raise serializers.ValidationError("Not found.")
        if rent_payment.status in self._BLOCKED_FOR_NEW_ATTEMPT_STATUSES:
            raise serializers.ValidationError(
                "This rent payment is already cleared or being processed."
            )
        return rent_payment

    def validate(self, attrs):
        request = self.context["request"]
        payment_method = PaymentMethod.objects.filter(
            tenant=request.user,
            provider=PaymentProviderChoices.GOCARDLESS,
            is_default=True,
        ).exclude(provider_mandate_id__isnull=True).exclude(provider_mandate_id="").first()

        if not payment_method:
            raise serializers.ValidationError(
                "No active direct debit mandate found. Please set up direct debit first."
            )
        attrs["payment_method"] = payment_method
        return attrs
