from django.db.models import Count, Prefetch, Q
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from api.serializers.marketplace import (
    MarketplaceCategorySerializer,
    MarketplaceProviderSerializer,
)
from apps.marketplace.models import MarketplaceCategory, MarketplaceProvider
from common.permission import IsSuperAdminOrLandlordReadOnly


def _active_categories(user):
    qs = MarketplaceCategory.objects.all()
    return qs if user.is_superuser else qs.filter(is_active=True)


def _active_providers(user):
    qs = MarketplaceProvider.objects.prefetch_related(
        Prefetch("categories", queryset=_active_categories(user))
    )
    return qs if user.is_superuser else qs.filter(is_active=True)


class MarketplaceCategoryListView(ListCreateAPIView):
    serializer_class = MarketplaceCategorySerializer
    permission_classes = [IsSuperAdminOrLandlordReadOnly]
    pagination_class = None
    filterset_fields = ["is_active"]
    search_fields = ["name", "description"]

    def get_queryset(self):
        user = self.request.user
        provider_filter = Q() if user.is_superuser else Q(providers__is_active=True)
        return _active_categories(user).annotate(
            provider_count=Count("providers", filter=provider_filter, distinct=True)
        )

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class MarketplaceCategoryDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = MarketplaceCategorySerializer
    permission_classes = [IsSuperAdminOrLandlordReadOnly]

    def get_object(self):
        return get_object_or_404(
            _active_categories(self.request.user),
            alias=self.kwargs["category_alias"],
        )

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class MarketplaceProviderListView(ListCreateAPIView):
    serializer_class = MarketplaceProviderSerializer
    permission_classes = [IsSuperAdminOrLandlordReadOnly]
    filterset_fields = {
        "categories__alias": ["exact"],
        "categories__slug": ["exact"],
        "is_verified": ["exact"],
        "is_featured": ["exact"],
        "is_active": ["exact"],
    }
    search_fields = ["name", "short_description", "description"]

    def get_queryset(self):
        return _active_providers(self.request.user).distinct()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class MarketplaceProviderDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = MarketplaceProviderSerializer
    permission_classes = [IsSuperAdminOrLandlordReadOnly]

    def get_object(self):
        return get_object_or_404(
            _active_providers(self.request.user),
            alias=self.kwargs["provider_alias"],
        )

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
