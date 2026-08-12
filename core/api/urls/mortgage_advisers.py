from django.urls import path

from ..views.mortgage_advisers import (
    MortgageAdviserPropertyListView,
    MortgageAdviserPropertyDetailView,
    MortgageAdviserMortgageListView,
    MortgageAdviserMortgageDetailView,
)

urlpatterns = [
    path("/property", MortgageAdviserPropertyListView.as_view()),
    path(
        "/property/<uuid:property_alias>",
        MortgageAdviserPropertyDetailView.as_view(),
    ),
    path("/mortgage", MortgageAdviserMortgageListView.as_view()),
    path(
        "/mortgage/<uuid:mortgage_alias>",
        MortgageAdviserMortgageDetailView.as_view(),
    ),
]
