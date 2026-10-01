from django.urls import path

from api.views.admin import LandloardView, LandloardDetailView

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
]