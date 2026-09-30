from django.urls import path

from api.views.admin import LandloardProfileView, LandloardProfileDetailView

urlpatterns = [
    path(
        "/Landloards",
        LandloardProfileView.as_view(),
        name="Landloard-Profile-View"
    ),
    path(
        "/Landloards/<uuid:landloard_alias>",
        LandloardProfileDetailView.as_view(),
        name="Landloard-Profile-Detail-View"
    ),
]