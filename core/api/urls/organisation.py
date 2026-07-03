from django.urls import path
from api.views.organisation import (
    OrganisationDetailView,
    OrganisationUserListView,
    OrganisationUserDetailView,
    OrganisationListView,
)

urlpatterns = [
    path("", OrganisationListView.as_view(), name="organisation-list"),
    path(
        "/<slug:organisation_slug>",
        OrganisationDetailView.as_view(),
        name="organisation-detail",
    ),
    path(
        "/<slug:organisation_slug>/users",
        OrganisationUserListView.as_view(),
        name="organisation-user-list",
    ),
    path(
        "/<slug:organisation_slug>/users/<uuid:alias>",
        OrganisationUserDetailView.as_view(),
        name="organisation-user-detail",
    ),
]
