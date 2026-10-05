from django.urls import path

from api.views.marketplace import (
    MarketplaceCategoryListView,
    MarketplaceCategoryDetailView,
    MarketplaceProviderListView,
    MarketplaceProviderDetailView,
)

urlpatterns = [
    path(
        "/categories",
        MarketplaceCategoryListView.as_view(),
        name="marketplace-category-list",
    ),
    path(
        "/categories/<uuid:category_alias>",
        MarketplaceCategoryDetailView.as_view(),
        name="marketplace-category-detail",
    ),
    path(
        "/providers",
        MarketplaceProviderListView.as_view(),
        name="marketplace-provider-list",
    ),
    path(
        "/providers/<uuid:provider_alias>",
        MarketplaceProviderDetailView.as_view(),
        name="marketplace-provider-detail",
    ),
]
