from django.urls import path

from ..views.mortgage_advisers import (
    MortgageAdviserPropertyPermissionView,
    MortgageAdviserMortgagePermissionView,
    MortgageAdviserPropertyPermissionListAPIView,
    MortgageAdviserMortgagePermissionListAPIView,
)

urlpatterns = [
    path(
        "/property/<uuid:property_alias>/permissions",
        MortgageAdviserPropertyPermissionListAPIView.as_view(),
        name="mortgage-adviser-property-permissions-list",
    ),
    path(
        "/<uuid:adviser_alias>/property/<uuid:property_alias>/permissions",
        MortgageAdviserPropertyPermissionView.as_view(),
        name="mortgage-adviser-property-permissions",
    ),
    path(
        "/mortgage/<uuid:mortgage_alias>/permissions",
        MortgageAdviserMortgagePermissionListAPIView.as_view(),
        name="mortgage-adviser-mortgage-permissions-list",
    ),
    path(
        "/<uuid:adviser_alias>/mortgage/<uuid:mortgage_alias>/permissions",
        MortgageAdviserMortgagePermissionView.as_view(),
        name="mortgage-adviser-mortgage-permissions",
    ),
]
