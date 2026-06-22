from django.urls import path
from api.views.organisation import OrganisationDetailView

urlpatterns = [
    path("", OrganisationDetailView.as_view(), name="organisation-detail"),
]
