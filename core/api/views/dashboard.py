from decimal import Decimal

from django.db.models import Count, Sum
from django.utils import timezone

from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import RetrieveAPIView

from apps.authentication.models import Permission
from apps.organisation.enums import OrganisationRoleChoices
from apps.organisation.models import OrganisationSubscription, OrganisationUser
from apps.supportticket.models import SupportTicket
from apps.property.models import (
    Property,
    Tenant,
    Mortgage,
    ComplianceAndCertification,
    UploadDocument,
    Finance,
)
from apps.property.enums import (
    StatusType,
    TransactionType,
    PropertyType,
    CertificateType,
    ProductType,
)
from apps.supportticket.enums import SupportTicketStatus

from common.permission import IsLandlord, IsMortgageAdviser

from ..serializers.dashboard import (
    LandlordDashboardSummarySerializer,
    LandLordPropertyTypeDashboardSerializer,
    LandlordComplianceTypeDashboardSerializer,
)


def has_full_access(user, organisation):
    """Landlords and admins see everything; other roles only see permitted objects."""
    return OrganisationUser.objects.filter(
        user=user,
        organisation=organisation,
        role__in=[
            OrganisationRoleChoices.LANDLORD,
            OrganisationRoleChoices.ADMIN,
        ],
    ).exists()


def get_accessible_properties(user, organisation):
    queryset = Property.objects.filter(organisation=organisation)

    if has_full_access(user, organisation):
        return queryset

    return queryset.filter(
        id__in=Permission.objects.filter(
            user=user,
            organisation=organisation,
            property__isnull=False,
            can_view=True,
        ).values("property_id")
    )


def get_accessible_mortgages(user, organisation):
    queryset = Mortgage.objects.filter(organisation=organisation)

    if has_full_access(user, organisation):
        return queryset

    return queryset.filter(
        id__in=Permission.objects.filter(
            user=user,
            organisation=organisation,
            mortgage__isnull=False,
            can_view=True,
        ).values("mortgage_id")
    )


class LandlordDashboardSummaryView(RetrieveAPIView):
    serializer_class = LandlordDashboardSummarySerializer
    permission_classes = [IsLandlord | IsMortgageAdviser]

    def get_object(self):
        user = self.request.user
        organisation = user.get_organisation()

        today = timezone.localdate()

        # ---------------------------------------------------------
        # Properties
        # ---------------------------------------------------------

        properties = get_accessible_properties(user, organisation)
        property_total = properties.count()
        property_occupied = properties.filter(status=StatusType.OCCUPIED).count()
        property_vacant = properties.filter(status=StatusType.VACANT).count()
        property_under_maintenance = properties.filter(
            status=StatusType.UNDER_MAINTENANCE
        ).count()

        # ---------------------------------------------------------
        # Mortgages
        # ---------------------------------------------------------

        mortgages = get_accessible_mortgages(user, organisation)
        mortgage_total = mortgages.count()
        mortgage_outstanding = mortgages.aggregate(total=Sum("outstanding_balance"))[
            "total"
        ] or Decimal("0.00")
        monthly_mortgage_payment = mortgages.aggregate(total=Sum("monthly_payment"))[
            "total"
        ] or Decimal("0.00")
        mortgage_product_type_counts = dict(
            mortgages.values("interest_rate_type")
            .annotate(count=Count("id"))
            .values_list("interest_rate_type", "count")
        )

        properties_data = {
            "total": property_total,
            "occupied": property_occupied,
            "vacant": property_vacant,
            "under_maintenance": property_under_maintenance,
        }
        mortgages_data = {
            "total": mortgage_total,
            "total_outstanding": mortgage_outstanding,
            "fixed_rate": mortgage_product_type_counts.get(ProductType.FIXED_RATE, 0),
            "variable_rate": mortgage_product_type_counts.get(
                ProductType.VARIABLE_RATE, 0
            ),
            "tracker": mortgage_product_type_counts.get(ProductType.TRACKER, 0),
            "offset": mortgage_product_type_counts.get(ProductType.OFFSET, 0),
        }

        # Mortgage advisers only see property and mortgage data
        if not has_full_access(user, organisation):
            return {
                "properties": properties_data,
                "mortgages": mortgages_data,
            }

        # ---------------------------------------------------------
        # Tenants
        # ---------------------------------------------------------

        tenants = Tenant.objects.filter(organisation=organisation)
        tenant_total = tenants.count()
        tenant_active = tenants.filter(is_active=True).count()
        tenant_inactive = tenants.filter(is_active=False).count()

        # ---------------------------------------------------------
        # Rental income
        # ---------------------------------------------------------

        monthly_rental_income = properties.aggregate(
            total=Sum("monthly_rental_income")
        )["total"] or Decimal("0.00")

        # ---------------------------------------------------------
        # Finance - current month
        # ---------------------------------------------------------

        current_month_finance = Finance.objects.filter(
            organisation=organisation,
            date__year=today.year,
            date__month=today.month,
        )

        current_month_income = current_month_finance.filter(
            type=TransactionType.INCOME
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

        current_month_expense = current_month_finance.filter(
            type=TransactionType.EXPENSE
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

        current_month_net = current_month_income - current_month_expense

        # ---------------------------------------------------------
        # Compliance
        # ---------------------------------------------------------

        compliance = ComplianceAndCertification.objects.filter(
            organisation=organisation
        )
        compliance_total = compliance.count()
        compliance_expired = compliance.filter(expiry_date__lt=today).count()
        expiring_soon_date = today + timezone.timedelta(days=30)
        compliance_expiring_soon = compliance.filter(
            expiry_date__gte=today,
            expiry_date__lte=expiring_soon_date,
        ).count()

        # ---------------------------------------------------------
        # Documents
        # ---------------------------------------------------------

        documents = UploadDocument.objects.filter(organisation=organisation)
        document_total = documents.count()

        # ---------------------------------------------------------
        # Subscription
        # ---------------------------------------------------------

        subscription = (
            OrganisationSubscription.objects.select_related("plan")
            .filter(organisation=organisation)
            .first()
        )

        # ---------------------------------------------------------
        # Support tickets
        # ---------------------------------------------------------

        tickets = SupportTicket.objects.filter(
            organisation=organisation,
            is_deleted=False,
        )
        ticket_open = tickets.filter(status=SupportTicketStatus.OPEN).count()
        ticket_in_progress = tickets.filter(
            status=SupportTicketStatus.IN_PROGRESS
        ).count()

        # ---------------------------------------------------------
        # Response
        # ---------------------------------------------------------

        return {
            "properties": properties_data,
            "mortgages": mortgages_data,
            "tenants": {
                "total": tenant_total,
                "active": tenant_active,
                "inactive": tenant_inactive,
            },
            "financial": {
                "monthly_rental_income": monthly_rental_income,
                "mortgage_outstanding": mortgage_outstanding,
                "monthly_mortgage_payment": monthly_mortgage_payment,
                "current_month_income": current_month_income,
                "current_month_expense": current_month_expense,
                "current_month_net": current_month_net,
            },
            "compliance": {
                "total": compliance_total,
                "expired": compliance_expired,
                "expiring_soon": compliance_expiring_soon,
            },
            "documents": {
                "total": document_total,
            },
            "subscription": {
                "plan": (subscription.plan.name if subscription else None),
                "status": (subscription.status if subscription else None),
                "current_period_end": (subscription.end_date if subscription else None),
            },
            "support": {
                "open": ticket_open,
                "in_progress": ticket_in_progress,
            },
        }


class LandlordPropertyTypeDashboardView(RetrieveAPIView):
    serializer_class = LandLordPropertyTypeDashboardSerializer
    permission_classes = [IsLandlord | IsMortgageAdviser]

    def get_object(self):
        organisation = self.request.user.get_organisation()

        queryset = (
            get_accessible_properties(self.request.user, organisation)
            .values("property_type")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        total = sum(item["count"] for item in queryset)

        data = []

        for item in queryset:
            property_type = item["property_type"]

            try:
                label = PropertyType(property_type).label
            except ValueError:
                label = property_type

            count = item["count"]

            percentage = round((count / total) * 100, 2) if total else 0

            data.append(
                {
                    "type": property_type,
                    "label": label,
                    "count": count,
                    "percentage": percentage,
                }
            )

        return {
            "total": total,
            "data": data,
        }


class LandlordComplianceTypeDashboardView(RetrieveAPIView):
    serializer_class = LandlordComplianceTypeDashboardSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        organisation = self.request.user.get_organisation()

        queryset = (
            ComplianceAndCertification.objects.filter(
                organisation=organisation,
            )
            .values("certificate_type")
            .annotate(
                count=Count("id"),
            )
            .order_by("-count")
        )

        total = sum(item["count"] for item in queryset)

        data = []

        for item in queryset:
            certificate_type = item["certificate_type"]

            try:
                label = CertificateType(certificate_type).label
            except ValueError:
                label = certificate_type

            count = item["count"]

            percentage = round((count / total) * 100, 2) if total else 0

            data.append(
                {
                    "type": certificate_type,
                    "label": label,
                    "count": count,
                    "percentage": percentage,
                }
            )

        return {
            "total": total,
            "data": data,
        }
