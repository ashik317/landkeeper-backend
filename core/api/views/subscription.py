from django.db import transaction

from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework import status
from rest_framework.response import Response

from apps.organisation.models import OrganisationSubscription
from apps.subscription.models import SubscriptionPlan

from common.permission import IsLandlord

from api.serializers.subscription import SubscriptionPlanSerializer, SelectSubscriptionSerializer


class SubscriptionPlanListView(ListAPIView):
    serializer_class = SubscriptionPlanSerializer
    permission_classes = []

    def get_queryset(self):
        return (
            SubscriptionPlan.objects.filter(is_active=True)
            .prefetch_related("features")
            .order_by("monthly_price")
        )


class SelectSubscriptionView(CreateAPIView):
    serializer_class = SelectSubscriptionSerializer
    permission_classes = [IsLandlord]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan = serializer.validated_data["plan"]

        organisation = request.user.get_organisation()

        if not organisation:
            return Response(
                {"detail": "Organisation not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        with transaction.atomic():
            subscription, created = OrganisationSubscription.objects.update_or_create(
                organisation=organisation,
                defaults={
                    "plan": plan,
                    "status": OrganisationSubscription.Status.PENDING,
                },
            )

        return Response(
            {
                "message": "Subscription plan selected successfully.",
                "subscription": {
                    "plan": plan.name,
                    "plan_type": plan.plan_type,
                    "monthly_price": plan.monthly_price,
                    "status": subscription.status,
                },
            },
            status=status.HTTP_201_CREATED,
        )
