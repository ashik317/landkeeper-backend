from django.urls import path

from ..views.mortgage_advisers import (
    MortgageAdviserPropertyPermissionView,
    MortgageAdviserMortgagePermissionView,
    MortgageAdviserPropertyListView,
    MortgageAdviserPropertyDetailView,
    MortgageAdviserMortgageListView,
    MortgageAdviserMortgageDetailView,
    MortgageAdviserPropertyPermissionListAPIView,
    MortgageAdviserMortgagePermissionListAPIView,
)

urlpatterns = [
    path(
        "/property/permissions",
        MortgageAdviserPropertyPermissionListAPIView.as_view(),
        name="mortgage-adviser-property-permissions-list",
    ),
    path(
        "/<uuid:adviser_alias>/property/<uuid:property_alias>/permissions",
        MortgageAdviserPropertyPermissionView.as_view(),
        name="mortgage-adviser-property-permissions",
    ),
    path(
    "/mortgage/permissions",
        MortgageAdviserMortgagePermissionListAPIView.as_view(),
        name="mortgage-adviser-mortgage-permissions-list",
    ),
    path(
        "/<uuid:adviser_alias>/mortgage/<uuid:mortgage_alias>/permissions",
        MortgageAdviserMortgagePermissionView.as_view(),
        name="mortgage-adviser-mortgage-permissions",
    ),
    path("/property", MortgageAdviserPropertyListView.as_view()),
    path(
        "/property/<uuid:property_alias>",
        MortgageAdviserPropertyDetailView.as_view(),
    ),
    path("/mortgage", MortgageAdviserMortgageListView.as_view()),
    path(
        "/mortgage/<uuid:mortgage_alias>",
        MortgageAdviserMortgageDetailView.as_view(),
    ),
]
