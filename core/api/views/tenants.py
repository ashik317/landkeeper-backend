import uuid
from datetime import date
from io import BytesIO
from django.http import FileResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)
from reportlab.lib.styles import getSampleStyleSheet
from rest_framework import generics, permissions, status
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    ListAPIView,
    RetrieveAPIView
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.tenant.gocardless_client import create_redirect_flow, complete_redirect_flow
from apps.tenant.models import PaymentMethod, RentPayment
from api.serializers.tenants import (
    PaymentMethodSerializer,
    RentPaymentSerializer,
    RentBalanceSummarySerializer,
    CardPaymentRequestSerializer,
    DirectDebitSetupRequestSerializer,
    DirectDebitCompleteRequestSerializer
)
from apps.tenant.permission import IsTenant
from apps.tenant.stripe_client import create_payment_intent
from apps.tenant.utils import get_statement_date_range


class PaymentMethodListCreateView(ListCreateAPIView):
    serializer_class = PaymentMethodSerializer
    permission_classes = [IsAuthenticated, IsTenant]

    def get_queryset(self):
        return PaymentMethod.objects.filter(tenant=self.request.user)

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user)


class PaymentMethodDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "alias"

    def get_queryset(self):
        return PaymentMethod.objects.filter(tenant=self.request.user)


class RentPaymentListCreateView(ListCreateAPIView):
    serializer_class = RentPaymentSerializer
    permission_classes = [IsAuthenticated, IsTenant]

    def get_queryset(self):
        return RentPayment.objects.filter(tenant=self.request.user)

    def perform_create(self, serializer):
        serializer.save(
            tenant=self.request.user,
            property=self.request.user.property,
            organisation=self.request.user.organisation,
        )


class RentPaymentDetailView(RetrieveAPIView):
    serializer_class = RentPaymentSerializer
    permission_classes = [IsAuthenticated, IsTenant]
    lookup_field = "alias"

    def get_queryset(self):
        return RentPayment.objects.filter(tenant=self.request.user)


class CardPaymentView(APIView):
    permission_classes = [IsAuthenticated, IsTenant]

    def post(self, request):
        serializer = CardPaymentRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        intent = create_payment_intent(
            amount=serializer.validated_data["amount"],
            payment_method_id=serializer.validated_data.get("payment_method_id"),
        )
        return Response(
            {"client_secret": intent.client_secret, "status": intent.status},
            status=status.HTTP_201_CREATED,
        )

class DirectDebitSetupView(APIView):
    permission_classes = [IsAuthenticated, IsTenant]

    def post(self, request):
        serializer = DirectDebitSetupRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tenant = request.user

        session_token = str(uuid.uuid4())

        flow = create_redirect_flow(
            tenant=tenant,
            session_token=session_token,
            success_redirect_url=serializer.validated_data["success_redirect_url"],
        )

        return Response(
            {
                "redirect_url": flow.redirect_url,
                "session_token": session_token
            },
            status=status.HTTP_201_CREATED
        )


class DirectDebitCompleteView(APIView):
    permission_classes = [IsAuthenticated, IsTenant]

    def post(self, request):
        serializer = DirectDebitCompleteRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tenant = request.user

        flow = complete_redirect_flow(
            serializer.validated_data["redirect_flow_id"],
            serializer.validated_data["session_token"],
        )

        PaymentMethod.objects.filter(tenant=tenant, is_default=True).update(
            is_default=False
        )

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
            status=status.HTTP_201_CREATED
        )

class DirectDebitCallbackView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        redirect_flow_id = request.GET.get("redirect_flow_id")

        return Response({
            "redirect_flow_id": redirect_flow_id
        })

class RentBalanceSummaryView(APIView):
    permission_classes = [IsAuthenticated, IsTenant]

    def get(self, request):
        tenant = request.user
        serializer = RentBalanceSummarySerializer(tenant)
        return Response(serializer.data)


class RentStatementView(APIView):
    """
    api/rent-statements/?period=yearly&year=2026
    api/rent-statements/?period=monthly&year=2026&month=7
    api/rent-statements/?period=weekly&year=2026&week=29
    api/rent-statements/?period=custom&start_date=2026-01-01&end_date=2026-03-31
    """
    permission_classes = [IsAuthenticated, IsTenant]

    def get(self, request):
        period = request.query_params.get("period", "yearly")

        try:
            start, end, label = get_statement_date_range(period, request.query_params)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)

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