from django.contrib import admin

from apps.marketplace.models import MarketplaceCategory, MarketplaceProvider


@admin.register(MarketplaceCategory)
class MarketplaceCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "display_order", "is_active", "created_at"]
    list_filter = ["is_active"]
    list_editable = ["display_order", "is_active"]
    search_fields = ["name", "description"]
    readonly_fields = ["alias", "slug", "created_at", "updated_at"]
    ordering = ["display_order", "name"]


@admin.register(MarketplaceProvider)
class MarketplaceProviderAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "is_active",
        "is_verified",
        "is_featured",
        "display_order",
        "created_at",
    ]
    list_filter = ["is_active", "is_verified", "is_featured", "categories"]
    list_editable = ["is_active", "is_verified", "is_featured", "display_order"]
    search_fields = ["name", "short_description", "description", "contact_email"]
    filter_horizontal = ["categories"]
    readonly_fields = ["alias", "slug", "created_at", "updated_at"]
    ordering = ["display_order", "name"]
