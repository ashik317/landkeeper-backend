from django.urls import path
from api.views.property import PropertyListCreateAPIView

urlpatterns = [
    path(
        "proprty/",
        PropertyListCreateAPIView.as_view(),
        name="property-list-create"
    ),
]