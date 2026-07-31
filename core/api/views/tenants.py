import calendar
import hashlib
import hmac
import json
import logging
import uuid
from io import BytesIO
import gocardless_pro
import stripe
from datetime import date, timedelta
from django.conf import settings
from django.db import IntegrityError, transaction
from django.http import FileResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)
from rest_framework import permissions, status
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
)
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView

from api.serializers.tenants import (
    PaymentMethodSerializer,
    RentPaymentSerializer,
    RentBalanceSummarySerializer,
    CardPaymentRequestSerializer,
    DirectDebitSetupRequestSerializer,
    DirectDebitCompleteRequestSerializer,
    DirectDebitPaymentRequestSerializer,
)
from apps.property.models import Tenant
from apps.tenant.enums import RentPaymentStatusChoices
from apps.tenant.gocardless_client import (
    create_redirect_flow,
    complete_redirect_flow,
    create_payment as create_gocardless_payment,
    cancel_mandate,
)
from apps.tenant.models import PaymentMethod, RentPayment, ProcessedWebhookEvent
from apps.tenant.permission import IsTenant
from apps.tenant.stripe_client import create_payment_intent
from apps.tenant.utils import get_statement_date_range

logger = logging.getLogger("apps.tenant.payments")

_TERMINAL_STATUSES = {
    RentPaymentStatusChoices.CLEARED,
    RentPaymentStatusChoices.REFUNDED,
}

class PaymentMethodListCreateView(ListAPIView):
    serializer_class = PaymentMethodSerializer
    permission_classes = [IsTenant]

    def get_queryset(self):
        return PaymentMethod.objects.filter(tenant=self.request.user)


class PaymentMethodDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = PaymentMethodSerializer
    permission_classes = [IsTenant]
    lookup_field = "alias"

    def get_queryset(self):
        return PaymentMethod.objects.filter(tenant=self.request.user)

    def perform_destroy(self, instance):
        if instance.provider == "GOCARDLESS" and instance.provider_mandate_id:
            try:
                cancel_mandate(instance.provider_mandate_id)
            except gocardless_pro.errors.GoCardlessProError:
                logger.exception(
                    "Failed to cancel GoCardless mandate on delete",
                    extra={"mandate_id": instance.provider_mandate_id},
                )
        instance.delete()


class RentPaymentListCreateView(ListCreateAPIView):
    serializer_class = RentPaymentSerializer
    permission_classes = [IsTenant]

    def get_queryset(self):
        return RentPayment.objects.filter(tenant=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def perform_create(self, serializer):
        serializer.save(
            tenant=self.request.user,
            property=self.request.user.property,
            organisation=self.request.user.organisation,
        )


class RentPaymentDetailView(RetrieveAPIView):
    serializer_class = RentPaymentSerializer
    permission_classes = [IsTenant]
    lookup_field = "alias"

    def get_queryset(self):
        return RentPayment.objects.filter(tenant=self.request.user)


class CardPaymentView(APIView):
    permission_classes = [IsTenant]

    def post(self, request):
        serializer = CardPaymentRequestSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        rent_payment = serializer.validated_data["rent_payment"]
        payment_method_id = serializer.validated_data.get("payment_method_id")

        try:
            intent = create_payment_intent(
                amount=serializer.validated_data["amount"],
                payment_method_id=payment_method_id,
                idempotency_key=f"card-{rent_payment.alias}",
                metadata={"rent_payment_alias": str(rent_payment.alias)},
            )
        except stripe.error.CardError as e:
            return Response(
                {"error": e.user_message or "Your card was declined."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except stripe.error.StripeError:
            return Response(
                {"error": "Payment provider error. Please try again."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        payment_method_obj = self._get_or_create_card_payment_method(
            tenant=rent_payment.tenant, payment_method_id=payment_method_id
        )

        updated = RentPayment.objects.filter(pk=rent_payment.pk).exclude(
            status__in=_TERMINAL_STATUSES
        ).update(
            provider_payment_id=intent.id,
            payment_method=payment_method_obj,
            status=RentPaymentStatusChoices.PROCESSING,
        )

        if not updated:
            logger.warning(
                "CardPaymentView: rent_payment already terminal, skipped status downgrade",
                extra={"rent_payment_alias": str(rent_payment.alias), "intent_id": intent.id},
            )

        return Response(
            {"client_secret": intent.client_secret, "status": intent.status},
            status=status.HTTP_201_CREATED,
        )

    @staticmethod
    def _get_or_create_card_payment_method(tenant, payment_method_id):
        if not payment_method_id:
            return None

        existing = PaymentMethod.objects.filter(
            tenant=tenant,
            provider="STRIPE",
            provider_payment_method_id=payment_method_id,
        ).first()
        if existing:
            return existing

        try:
            stripe_pm = stripe.PaymentMethod.retrieve(payment_method_id)
        except stripe.error.StripeError:
            logger.exception(
                "Failed to fetch Stripe PaymentMethod details",
                extra={"payment_method_id": payment_method_id},
            )
            return None

        card = getattr(stripe_pm, "card", None)

        return PaymentMethod.objects.create(
            tenant=tenant,
            provider="STRIPE",
            method_type="CARD",
            provider_payment_method_id=payment_method_id,
            status="ACTIVE",
            is_default=False,
            card_last4=getattr(card, "last4", None) if card else None,
            card_brand=getattr(card, "brand", None) if card else None,
        )


class DirectDebitSetupView(APIView):
    permission_classes = [IsTenant]

    def post(self, request):
        serializer = DirectDebitSetupRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tenant = request.user
        session_token = str(uuid.uuid4())

        try:
            flow = create_redirect_flow(
                tenant=tenant,
                session_token=session_token,
                success_redirect_url=serializer.validated_data["success_redirect_url"],
            )
        except gocardless_pro.errors.GoCardlessProError:
            logger.exception("GoCardless create_redirect_flow failed", extra={"tenant_id": tenant.id})
            return Response(
                {"error": "Payment provider error. Please try again."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(
            {"redirect_url": flow.redirect_url, "session_token": session_token},
            status=status.HTTP_201_CREATED,
        )


class DirectDebitCompleteView(APIView):
    permission_classes = [IsTenant]

    def post(self, request):
        serializer = DirectDebitCompleteRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tenant = request.user

        try:
            flow = complete_redirect_flow(
                serializer.validated_data["redirect_flow_id"],
                serializer.validated_data["session_token"],
            )
        except gocardless_pro.errors.InvalidStateError:
            return Response(
                {"error": "This direct debit setup link has expired or already been used."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except gocardless_pro.errors.GoCardlessProError:
            logger.exception("GoCardless complete_redirect_flow failed", extra={"tenant_id": tenant.id})
            return Response(
                {"error": "Payment provider error. Please try again."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        with transaction.atomic():
            PaymentMethod.objects.select_for_update().filter(
                tenant=tenant, is_default=True
            ).update(is_default=False)

            payment_method = PaymentMethod.objects.create(
                tenant=tenant,
                provider="GOCARDLESS",
                method_type="DIRECT_DEBIT",
                provider_customer_id=flow.links.customer,
                provider_mandate_id=flow.links.mandate,
                status="ACTIVE",
                is_default=True,
            )

        return Response(
            PaymentMethodSerializer(payment_method).data,
            status=status.HTTP_201_CREATED,
        )

class DirectDebitPaymentView(APIView):
    permission_classes = [IsTenant]

    def post(self, request):
        serializer = DirectDebitPaymentRequestSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        rent_payment = serializer.validated_data["rent_payment"]
        payment_method = serializer.validated_data["payment_method"]

        try:
            payment = create_gocardless_payment(
                mandate_id=payment_method.provider_mandate_id,
                amount=rent_payment.amount,
                idempotency_key=f"dd-{rent_payment.alias}",
                metadata={"rent_payment_alias": str(rent_payment.alias)},
            )
        except gocardless_pro.errors.InvalidStateError as e:
            return Response(
                {"error": "Mandate is not active. Please set up direct debit again.", "detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except gocardless_pro.errors.GoCardlessProError:
            return Response(
                {"error": "Payment provider error. Please try again."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        updated = RentPayment.objects.filter(pk=rent_payment.pk).exclude(
            status__in=_TERMINAL_STATUSES
        ).update(
            provider_payment_id=payment.id,
            payment_method=payment_method,
            status=RentPaymentStatusChoices.PROCESSING,
        )

        if not updated:
            logger.warning(
                "DirectDebitPaymentView: rent_payment already terminal, skipped status downgrade",
                extra={"rent_payment_alias": str(rent_payment.alias), "payment_id": payment.id},
            )

        return Response(
            {"provider_payment_id": payment.id, "status": payment.status},
            status=status.HTTP_201_CREATED,
        )


class DirectDebitCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        redirect_flow_id = request.GET.get("redirect_flow_id")
        return Response({"redirect_flow_id": redirect_flow_id})


class RentBalanceSummaryView(APIView):
    permission_classes = [IsTenant]

    def get(self, request):
        serializer = RentBalanceSummarySerializer(request.user)
        return Response(serializer.data)


class RentStatementView(APIView):
    """
    api/rent-statements/?period=yearly&year=2026
    api/rent-statements/?period=monthly&year=2026&month=7
    api/rent-statements/?period=weekly&year=2026&week=29
    api/rent-statements/?period=custom&start_date=2026-01-01&end_date=2026-03-31
    """
    permission_classes = [IsTenant]

    def get(self, request):
        period = request.query_params.get("period", "yearly")

        try:
            start, end, label = get_statement_date_range(period, request.query_params)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        tenant = request.user
        payments = RentPayment.objects.filter(
            tenant=tenant, due_date__gte=start, due_date__lte=end
        ).order_by("due_date")

        buffer = self.build_rent_statement_pdf(tenant, payments, period_label=label)
        filename = f"rent_statement_{period}_{start}_{end}.pdf"
        return FileResponse(buffer, as_attachment=True, filename=filename)

    @staticmethod
    def build_rent_statement_pdf(tenant, payments, period_label):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph(f"Rent Statement — {period_label}", styles["Title"]))
        elements.append(Paragraph(f"Tenant: {tenant}", styles["Normal"]))
        elements.append(Spacer(1, 12))

        data = [["Date", "Reference", "Amount", "Status"]]
        total = 0
        for p in payments:
            data.append([
                p.paid_date.strftime("%d %b %Y") if p.paid_date else p.due_date.strftime("%d %b %Y"),
                p.reference,
                f"£{p.amount:,.2f}",
                p.get_status_display(),
            ])
            total += p.amount

        data.append(["", "", f"Total: £{total:,.2f}", ""])

        table = Table(data, colWidths=[80, 160, 100, 100])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -2), 0.5, colors.grey),
            ("FONTNAME", (-2, -1), (-2, -1), "Helvetica-Bold"),
            ("ALIGN", (2, 0), (2, -1), "RIGHT"),
        ]))
        elements.append(table)

        doc.build(elements)
        buffer.seek(0)
        return buffer


class WebhookRateThrottle(SimpleRateThrottle):
    scope = "webhook"

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [WebhookRateThrottle]

    def post(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except (ValueError, stripe.error.SignatureVerificationError):
            logger.warning("Stripe webhook signature verification failed")
            return Response(
                {"error": "Invalid payload or signature"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            event_type = event["type"]
            data_object = event["data"]["object"]
        except (KeyError, TypeError):
            logger.warning("Stripe webhook malformed payload", extra={"event_id": event.get("id")})
            return Response(
                {"error": "Malformed event payload"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                if not self._claim_event(event["id"]):
                    return Response({"received": True, "duplicate": True}, status=status.HTTP_200_OK)

                if event_type == "payment_intent.succeeded":
                    self._mark_payment(data_object["id"], RentPaymentStatusChoices.CLEARED)
                elif event_type == "payment_intent.payment_failed":
                    self._mark_payment(
                        data_object["id"],
                        RentPaymentStatusChoices.FAILED,
                        failure_reason=data_object.get("last_payment_error", {}).get(
                            "message", "Payment failed"
                        ),
                    )
        except Exception:
            logger.exception("Stripe webhook processing failed", extra={"event_id": event.get("id")})
            return Response({"error": "Processing error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"received": True}, status=status.HTTP_200_OK)

    @staticmethod
    def _claim_event(event_id):
        try:
            ProcessedWebhookEvent.objects.create(provider="stripe", event_id=event_id)
            return True
        except IntegrityError:
            return False

    @staticmethod
    def _mark_payment(provider_payment_id, new_status, failure_reason=None):
        update_fields = {"status": new_status}
        if new_status == RentPaymentStatusChoices.CLEARED:
            update_fields["paid_date"] = timezone.localdate()
        if failure_reason:
            update_fields["failure_reason"] = failure_reason

        updated = RentPayment.objects.filter(
            provider_payment_id=provider_payment_id
        ).exclude(status__in=_TERMINAL_STATUSES).update(**update_fields)

        if not updated:
            logger.warning(
                "Stripe webhook: no matching non-terminal RentPayment",
                extra={"provider_payment_id": provider_payment_id, "new_status": new_status},
            )


@method_decorator(csrf_exempt, name="dispatch")
class GoCardlessWebhookView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [WebhookRateThrottle]

    def post(self, request):
        raw_body = request.body
        signature = request.META.get("HTTP_WEBHOOK_SIGNATURE", "")

        if not self._is_valid_signature(raw_body, signature):
            logger.warning("GoCardless webhook signature verification failed")
            return Response(
                {"error": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError:
            return Response(
                {"error": "Malformed JSON payload"}, status=status.HTTP_400_BAD_REQUEST
            )

        events = payload.get("events", [])

        for event in events:
            event_id = event.get("id")
            if not event_id:
                continue

            try:
                with transaction.atomic():
                    if not self._claim_event(event_id):
                        continue

                    resource_type = event.get("resource_type")
                    action = event.get("action")
                    links = event.get("links", {})

                    if resource_type == "payments":
                        provider_payment_id = links.get("payment")

                        if action == "confirmed":
                            self._mark_payment(
                                provider_payment_id, RentPaymentStatusChoices.CLEARED
                            )
                        elif action == "failed":
                            self._mark_payment(
                                provider_payment_id,
                                RentPaymentStatusChoices.FAILED,
                                failure_reason="Direct debit payment failed",
                            )
            except Exception:
                logger.exception("GoCardless webhook event processing failed", extra={"event_id": event_id})
                continue

        return Response({"received": True}, status=status.HTTP_200_OK)

    @staticmethod
    def _claim_event(event_id):
        try:
            ProcessedWebhookEvent.objects.create(provider="gocardless", event_id=event_id)
            return True
        except IntegrityError:
            return False

    @staticmethod
    def _is_valid_signature(raw_body, signature):
        secret = settings.GOCARDLESS_WEBHOOK_SECRET.encode()
        computed = hmac.new(secret, raw_body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(computed, signature)

    @staticmethod
    def _mark_payment(provider_payment_id, new_status, failure_reason=None):
        if not provider_payment_id:
            return

        update_fields = {"status": new_status}
        if new_status == RentPaymentStatusChoices.CLEARED:
            update_fields["paid_date"] = timezone.localdate()
        if failure_reason:
            update_fields["failure_reason"] = failure_reason

        updated = RentPayment.objects.filter(
            provider_payment_id=provider_payment_id
        ).exclude(status__in=_TERMINAL_STATUSES).update(**update_fields)

        if not updated:
            logger.warning(
                "GoCardless webhook: no matching non-terminal RentPayment",
                extra={"provider_payment_id": provider_payment_id, "new_status": new_status},
            )


ENDING_SOON_DAYS = 30
class PropertyTenancyListView(APIView):
    permission_classes = [IsTenant]

    def get(self, request):
        today = date.today()
        tenants = (
            Tenant.objects
            .select_related("property")
            .filter(id=request.user.id)
        )

        results = []
        for tenant in tenants:
            tenancy_term = None
            length = None
            status = "Inactive"

            if tenant.tenancy_start_date and tenant.tenancy_end_date:
                tenancy_term = (
                    f"{tenant.tenancy_start_date:%b %-d, %Y} - "
                    f"{tenant.tenancy_end_date:%b %-d, %Y}"
                )
                months = round(
                    (tenant.tenancy_end_date - tenant.tenancy_start_date).days / 30
                )
                length = f"{months}-month agreement"

                if tenant.tenancy_end_date < today:
                    status = "Expired"
                elif tenant.tenancy_end_date <= today + timedelta(days=ENDING_SOON_DAYS):
                    status = "Ending soon"
                elif tenant.tenancy_start_date <= today:
                    status = "Active"

            results.append({
                "tenant_id": tenant.id,
                "property_address": tenant.property.address,
                "tenancy_term": tenancy_term,
                "length": length,
                "status": status,
            })

        return Response(results)


class FinancialOverviewListView(APIView):
    permission_classes = [IsTenant]

    def get(self, request):
        today = date.today()
        tenants = (
            Tenant.objects
            .select_related("property")
            .filter(id=request.user.id)
        )

        results = []
        for tenant in tenants:
            payments = RentPayment.objects.filter(tenant=tenant).order_by("-due_date")[:10]

            outstanding_balance = sum(
                p.amount for p in payments if p.status not in _TERMINAL_STATUSES
            )

            next_rent_due_date = None
            upcoming = (
                RentPayment.objects
                .filter(tenant=tenant, due_date__gte=today)
                .exclude(status__in=_TERMINAL_STATUSES)
                .order_by("due_date")
                .first()
            )
            if upcoming:
                next_rent_due_date = upcoming.due_date
            elif tenant.tenancy_start_date:
                rent_day = tenant.tenancy_start_date.day
                year, month = today.year, today.month
                last_day_this_month = calendar.monthrange(year, month)[1]
                due_this_month = date(year, month, min(rent_day, last_day_this_month))

                if due_this_month >= today:
                    next_rent_due_date = due_this_month
                else:
                    month += 1
                    if month > 12:
                        month = 1
                        year += 1
                    last_day_next_month = calendar.monthrange(year, month)[1]
                    next_rent_due_date = date(year, month, min(rent_day, last_day_next_month))

            results.append({
                "tenant_id": tenant.id,
                "next_rent_due_date": next_rent_due_date,
                "outstanding_balance": outstanding_balance,
                "rent_amount": tenant.rent_amount,
            })

        return Response(results)