from django.urls import path
from api.views.organisation import (
    OrganisationOnboardingListAPIView,
    OrganisationOnboardingDetailAPIView
)

urlpatterns = [
    path(
        "onboard/",
        OrganisationOnboardingListAPIView.as_view(),
        name="organisation-list-create"
    ),
    path(
        "onboard/<slug:slug>/",
         OrganisationOnboardingDetailAPIView.as_view(),
        name="organisation-detail"
    ),
]