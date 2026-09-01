from django.urls import path

from api.views.subscription import SubscriptionPlanListView, SelectSubscriptionView


urlpatterns = [
    path(
        "/plans",
        SubscriptionPlanListView.as_view(),
        name="subscription-plan-list",
    ),
    path(
        "/plans/select",
        SelectSubscriptionView.as_view(),
        name="select-subscription",
    ),
]
