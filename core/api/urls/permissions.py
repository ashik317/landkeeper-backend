from django.urls import path

from ..views.permissions import (
    PermissionListAPIView,
    PermissionDetailView,
    PropertyPermissionListAPIView,
    MortgagePermissionListAPIView,
    BulkPropertyPermissionView,
    BulkMortgagePermissionView,
)

urlpatterns = [
    path(
        "",
        PermissionListAPIView.as_view(),
    ),
    path(
        "/<uuid:permission_alias>",
        PermissionDetailView.as_view(),
    ),
    path(
        "/property/<uuid:property_alias>",
        PropertyPermissionListAPIView.as_view(),
    ),
    path(
        "/user/<uuid:user_alias>/bulk-property",
        BulkPropertyPermissionView.as_view(),
    ),
    path(
        "/mortgage/<uuid:mortgage_alias>",
        MortgagePermissionListAPIView.as_view(),
    ),
    path(
        "/user/<uuid:user_alias>/bulk-mortgage",
        BulkMortgagePermissionView.as_view(),
    ),
]
