from rest_framework import serializers

from apps.marketplace.models import MarketplaceCategory, MarketplaceProvider


class MarketplaceCategorySlimSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketplaceCategory
        fields = ["alias", "name", "slug", "icon"]


class MarketplaceCategorySerializer(serializers.ModelSerializer):
    provider_count = serializers.IntegerField(read_only=True)
    # Explicit default so multipart requests omitting it don't read as False.
    is_active = serializers.BooleanField(default=True)

    class Meta:
        model = MarketplaceCategory
        fields = [
            "alias",
            "name",
            "slug",
            "description",
            "icon",
            "display_order",
            "is_active",
            "provider_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["alias", "slug", "created_at", "updated_at"]


class MarketplaceProviderSerializer(serializers.ModelSerializer):
    categories = MarketplaceCategorySlimSerializer(many=True, read_only=True)
    category_aliases = serializers.SlugRelatedField(
        slug_field="alias",
        queryset=MarketplaceCategory.objects.all(),
        many=True,
        write_only=True,
        required=False,
        source="categories",
    )
    services_offered = serializers.ListField(
        child=serializers.CharField(max_length=255), required=False
    )
    outbound_url = serializers.CharField(read_only=True)
    # Explicit default so multipart requests omitting it don't read as False.
    is_active = serializers.BooleanField(default=True)

    class Meta:
        model = MarketplaceProvider
        fields = [
            "alias",
            "name",
            "slug",
            "logo",
            "short_description",
            "description",
            "services_offered",
            "website_url",
            "referral_url",
            "outbound_url",
            "contact_email",
            "contact_phone",
            "address",
            "is_verified",
            "is_featured",
            "is_active",
            "display_order",
            "categories",
            "category_aliases",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["alias", "slug", "created_at", "updated_at"]

    def validate(self, attrs):
        website_url = attrs.get(
            "website_url", getattr(self.instance, "website_url", None)
        )
        referral_url = attrs.get(
            "referral_url", getattr(self.instance, "referral_url", None)
        )
        if not website_url and not referral_url:
            raise serializers.ValidationError(
                {"website_url": "A website link or referral link is required."}
            )
        return attrs
