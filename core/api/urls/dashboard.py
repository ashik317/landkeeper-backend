from django.urls import path

from ..views.dashboard import (
    LandlordDashboardSummaryView,
    LandlordPropertyTypeDashboardView,
    LandlordComplianceTypeDashboardView,
)

urlpatterns = [
    path(
        "/landlord/summary",
        LandlordDashboardSummaryView.as_view(),
        name="landlord-dashboard-summary",
    ),
    path(
        "/landlord/property-types",
        LandlordPropertyTypeDashboardView.as_view(),
        name="dashboard-property-types",
    ),
    path(
        "/landlord/compliance-types",
        LandlordComplianceTypeDashboardView.as_view(),
        name="dashboard-compliance-types",
    ),
]
