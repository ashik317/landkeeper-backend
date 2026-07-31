from django.urls import path
from api.views.documents import (
    DocumentsListCreateAPIView,
    DocumentsRetrieveUpdateDestroyAPIView
)

urlpatterns = [
    path(
        "",
        DocumentsListCreateAPIView.as_view(),
        name="document-list-create"
    ),
    path(
        "/<uuid:alias>",
        DocumentsRetrieveUpdateDestroyAPIView.as_view(),
        name="document-detail"
    ),
]