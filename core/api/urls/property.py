from django.urls import path
from api.views.property import (
    PropertyListView,
    PropertyDetailView,
    MortgageListView,
    MortgageDetailView,
    TenantListView,
    TenantDetailView,
    ComplianceAndCertificationListView,
    ComplianceAndCertificationDetailView,
)

urlpatterns = [
    path("/property", PropertyListView.as_view()),
    path(
        "/property/<uuid:property_alias>",
        PropertyDetailView.as_view(),
        name="property-retrieve-update",
    ),
    path("/mortgage", MortgageListView.as_view()),
    path(
        "/mortgage/<uuid:mortgage_alias>",
        MortgageDetailView.as_view(),
        name="mortgage-retrieve-update",
    ),
    path("/tenants", TenantListView.as_view()),
    path(
        "/tenants/<uuid:tenant_alias>",
        TenantDetailView.as_view(),
    ),
    path(
        "/compliance",
        ComplianceAndCertificationListView.as_view(),
    ),
    path(
        "/compliance/<uuid:compliance_alias>",
        ComplianceAndCertificationDetailView.as_view(),
    ),
]
