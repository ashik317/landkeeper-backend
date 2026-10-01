from django.urls import path

from api.views.admin import (
    LandloardView,
    LandloardDetailView,
    SuperAdminLandlordPropertyView,
    SuperAdminLandlordPropertyDetailView
)

urlpatterns = [
    path(
        "/landloards",
        LandloardView.as_view(),
        name="Landloard-View"
    ),
    path(
        "/landloards/<uuid:landloard_alias>",
        LandloardDetailView.as_view(),
        name="Landloard-Detail-View"
    ),
    path(
        "/landloards/<uuid:landlord_alias>/properties",
        SuperAdminLandlordPropertyView.as_view(),
        name="superadmin-landlord-properties",
    ),
    path(
        "/landloards/<uuid:landlord_alias>/properties/<uuid:property_alias>/",
        SuperAdminLandlordPropertyDetailView.as_view(),
        name="superadmin-landlord-property-detail",
    ),
]