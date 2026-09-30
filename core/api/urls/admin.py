from django.urls import path

from api.views.admin import LandloardView, LandloardDetailView

urlpatterns = [
    path(
        "/Landloards",
        LandloardView.as_view(),
        name="Landloard-View"
    ),
    path(
        "/Landloards/<uuid:landloard_alias>",
        LandloardDetailView.as_view(),
        name="Landloard-Detail-View"
    ),
]