import math

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from apps.organisation.models import OrganisationSubscription


User = get_user_model()


class LandloardProfileSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    is_password_available = serializers.SerializerMethodField()
    has_subscription = serializers.SerializerMethodField()
    subscription_status = serializers.SerializerMethodField()
    plan = serializers.SerializerMethodField()
    trial_days_left = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "alias",
            "email",
            "title",
            "first_name",
            "middle_name",
            "last_name",
            "current_address",
            "ni_number",
            "utr_number",
            "role",
            "phone",
            "profile_image",
            "is_active",
            "is_password_available",
            "has_subscription",
            "subscription_status",
            "plan",
            "trial_days_left",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "alias",
            "email",
            "role",
            "is_active",
            "created_at",
            "updated_at",
        ]

    def get_role(self, obj):
        if obj.is_superuser:
            return "SUPER_ADMIN"

        organisation_user = obj.organisation_users.first()

        return organisation_user.role if organisation_user else None

    def get_is_password_available(self, obj):
        return obj.has_usable_password()

    def get_has_subscription(self, obj):
        if obj.is_superuser:
            return False

        organisation = obj.get_organisation()

        if not organisation:
            return False

        return hasattr(organisation, "subscription")

    def get_subscription_status(self, obj):
        if obj.is_superuser:
            return None

        organisation = obj.get_organisation()

        if not organisation:
            return None

        subscription = getattr(organisation, "subscription", None)

        return subscription.status if subscription else None

    def get_plan(self, obj):
        if obj.is_superuser:
            return None

        organisation = obj.get_organisation()

        if not organisation:
            return None

        subscription = getattr(organisation, "subscription", None)

        return subscription.plan.plan_type if subscription else None

    def get_trial_days_left(self, obj):
        if obj.is_superuser:
            return None

        organisation = obj.get_organisation()

        if not organisation:
            return None

        subscription = getattr(organisation, "subscription", None)

        if not subscription:
            return None

        if (
            subscription.status != OrganisationSubscription.Status.TRIALING
            or not subscription.trial_end_date
        ):
            return None

        remaining = subscription.trial_end_date - timezone.now()

        if remaining.total_seconds() <= 0:
            return 0

        return math.ceil(remaining.total_seconds() / 86400)