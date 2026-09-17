import uuid
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.utils import timezone
import stripe
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
from rest_framework.generics import (
    ListAPIView,
    RetrieveUpdateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from api.serializers.subscription import (
    SubscriptionPlanSerializer,
    PaymentCardSerializer,
    BillingHistorySerializer,
    OrganisationSubscriptionStatusSerializer,
)
from apps.organisation.enums import OrganisationSubscriptionStatus
from apps.organisation.stripe_service import (
    handle_payment_success,
    handle_payment_failed,
    handle_invoice_payment_succeeded,
    handle_invoice_payment_failed,
    handle_subscription_deleted,
    handle_subscription_updated,
    create_subscription_with_client_secret,
    change_subscription_plan,
    PlanDowngradeBlockedError,
)
from apps.subscription.models import SubscriptionPlan, PaymentCard, PaymentTransaction
from apps.organisation.models import OrganisationSubscription
from apps.property.models import Property
from common.permission import IsLandlord


class SelectSubscriptionView(APIView):

    def post(self, request):
        plan_id = request.data.get("plan_id")
        payment_method_id = request.data.get("payment_method_id")

        if not plan_id:
            return Response(
                {"detail": "plan_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            plan = SubscriptionPlan.objects.get(alias=plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return Response(
                {"detail": "Subscription plan not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        organisation = request.user.get_organisation()

        current_subscription = (
            OrganisationSubscription.objects.filter(organisation=organisation)
            .select_related("plan")
            .first()
        )

        if current_subscription:

            if current_subscription.status in (
                OrganisationSubscriptionStatus.ACTIVE,
                OrganisationSubscriptionStatus.TRIALING,
            ):
                now = timezone.now()

                if (
                    current_subscription.status
                    == OrganisationSubscriptionStatus.TRIALING
                ):
                    period_over = (
                        current_subscription.trial_end_date is not None
                        and now >= current_subscription.trial_end_date
                    )
                else:
                    period_over = (
                        current_subscription.next_billing_date is not None
                        and now >= current_subscription.next_billing_date
                    )

                if not period_over:

                    if current_subscription.plan_id == plan.id:
                        return Response(
                            {"detail": "You are already subscribed to this plan."},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    try:
                        result = change_subscription_plan(organisation, plan)
                    except PlanDowngradeBlockedError as exc:
                        return Response(
                            {
                                "detail": (
                                    f"Cannot switch to '{plan.name}'. "
                                    f"You currently have {exc.current_property_count} "
                                    f"properties, but this plan only allows "
                                    f"{exc.max_properties}. Please remove "
                                    f"{exc.excess} properties before downgrading."
                                ),
                                "current_property_count": exc.current_property_count,
                                "new_plan_max_properties": exc.max_properties,
                                "properties_to_remove": exc.excess,
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    return Response(
                        {
                            "detail": (
                                "Plan upgraded successfully."
                                if result["is_upgrade"]
                                else "Plan downgraded successfully."
                            ),
                            "is_upgrade": result["is_upgrade"],
                            "account_credit": str(result["account_credit"]),
                            "requires_action": result["requires_action"],
                            "client_secret": result["client_secret"],
                        },
                        status=status.HTTP_200_OK,
                    )

            if current_subscription.plan_id != plan.id:
                current_property_count = organisation.organisation_properties.count()

                if plan.max_properties < current_property_count:
                    excess = current_property_count - plan.max_properties
                    return Response(
                        {
                            "detail": (
                                f"Cannot switch to '{plan.name}'. "
                                f"You currently have {current_property_count} "
                                f"properties, but this plan only allows "
                                f"{plan.max_properties}. Please remove "
                                f"{excess} properties before downgrading."
                            ),
                            "current_property_count": current_property_count,
                            "new_plan_max_properties": plan.max_properties,
                            "properties_to_remove": excess,
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            result = create_subscription_with_client_secret(
                organisation=organisation,
                user=request.user,
                plan=plan,
                payment_method_id=payment_method_id,
            )
            return Response(
                {
                    "subscription_id": result["subscription_id"],
                    "client_secret": result["client_secret"],
                    "mode": result["mode"],
                },
                status=status.HTTP_200_OK,
            )

        # No subscription at all yet
        result = create_subscription_with_client_secret(
            organisation=organisation,
            user=request.user,
            plan=plan,
            payment_method_id=payment_method_id,
        )
        return Response(
            {
                "subscription_id": result["subscription_id"],
                "client_secret": result["client_secret"],
                "mode": result["mode"],
            },
            status=status.HTTP_200_OK,
        )


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(View):

    def post(self, request, *args, **kwargs):
        payload = request.body
        signature = request.META.get("HTTP_STRIPE_SIGNATURE")

        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                settings.STRIPE_WEBHOOK_SECRET,
            )
        except ValueError:
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError:
            return HttpResponse(status=400)

        event_type = event["type"]
        data = event["data"]["object"]

        # Keep old handlers for backward compat / direct PI events
        if event_type == "payment_intent.succeeded":
            handle_payment_success(data)

        elif event_type == "payment_intent.payment_failed":
            handle_payment_failed(data)

        elif event_type in ("invoice.payment_succeeded", "invoice.paid"):
            handle_invoice_payment_succeeded(data)

        elif event_type == "invoice.payment_failed":
            handle_invoice_payment_failed(data)

        elif event_type == "customer.subscription.deleted":
            handle_subscription_deleted(data)

        elif event_type == "customer.subscription.updated":
            handle_subscription_updated(data)

        return HttpResponse(status=200)


class SubscriptionPlanListView(ListAPIView):
    serializer_class = SubscriptionPlanSerializer
    # permission_classes = []

    def get_queryset(self):
        return (
            SubscriptionPlan.objects.filter(is_active=True)
            .prefetch_related("features")
            .order_by("monthly_price")
        )


class LandlordPaymentCardListAPIView(APIView):
    permission_classes = [IsLandlord]

    def get(self, request):
        organisation = request.user.get_organisation()

        cards = PaymentCard.objects.filter(organisation=organisation).order_by(
            "-is_default", "-id"
        )

        serializer = PaymentCardSerializer(cards, many=True)

        return Response(
            {
                "cards": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class LandlordPaymentCardUpdateDeleteAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsLandlord]
    serializer_class = PaymentCardSerializer
    http_method_names = ["get", "patch", "delete"]
    lookup_field = "alias"
    lookup_url_kwarg = "alias"

    def get_queryset(self):
        organisation = self.request.user.get_organisation()
        return PaymentCard.objects.filter(organisation=organisation)

    def update(self, request, *args, **kwargs):
        organisation = self.request.user.get_organisation()
        instance = self.get_object()

        make_default = request.data.get("is_default", True)

        if make_default:
            return self._set_default(organisation, instance)
        else:
            return self._unset_default(organisation, instance)

    def _set_default(self, organisation, instance):
        if instance.is_default:
            return Response(
                {"detail": "This card is already the default."},
                status=status.HTTP_200_OK,
            )

        try:
            stripe.Customer.modify(
                organisation.stripe_customer_id,
                invoice_settings={
                    "default_payment_method": instance.stripe_payment_method_id
                },
            )
        except stripe.error.StripeError as exc:
            return Response(
                {"detail": f"Payment provider error: {exc.user_message or str(exc)}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        with transaction.atomic():
            PaymentCard.objects.filter(
                organisation=organisation, is_default=True
            ).exclude(pk=instance.pk).update(is_default=False)

            instance.is_default = True
            instance.save(update_fields=["is_default"])

        serializer = self.get_serializer(instance)
        return Response(
            {
                "detail": "Default payment method updated.",
                "card": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def _unset_default(self, organisation, instance):
        if not instance.is_default:
            return Response(
                {"detail": "This card is not currently the default."},
                status=status.HTTP_200_OK,
            )

        with transaction.atomic():
            instance.is_default = False
            instance.save(update_fields=["is_default"])

        try:
            stripe.Customer.modify(
                organisation.stripe_customer_id,
                invoice_settings={"default_payment_method": ""},
            )
        except stripe.error.StripeError:
            pass

        serializer = self.get_serializer(instance)
        return Response(
            {
                "detail": "Default payment method removed. No card is currently set as default.",
                "card": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def perform_destroy(self, instance):
        organisation = self.request.user.get_organisation()
        was_default = instance.is_default

        stripe.PaymentMethod.detach(instance.stripe_payment_method_id)
        instance.delete()

        if was_default:
            new_default = (
                PaymentCard.objects.filter(organisation=organisation)
                .order_by("-created_at")
                .first()
            )

            if new_default:
                new_default.is_default = True
                new_default.save(update_fields=["is_default"])

                stripe.Customer.modify(
                    organisation.stripe_customer_id,
                    invoice_settings={
                        "default_payment_method": (new_default.stripe_payment_method_id)
                    },
                )


class LandlordBillingHistoryAPIView(ListAPIView):
    serializer_class = BillingHistorySerializer
    permission_classes = [IsLandlord]

    def get_queryset(self):
        organisation = self.request.user.get_organisation()

        return (
            PaymentTransaction.objects.filter(
                organisation=organisation,
            )
            .select_related(
                "subscription",
                "subscription__plan",
            )
            .order_by("-created_at")
        )


class LandlordSubscriptionAPIView(RetrieveUpdateAPIView):
    serializer_class = OrganisationSubscriptionStatusSerializer
    permission_classes = [IsLandlord]

    def get_object(self):
        organisation = self.request.user.get_organisation()

        return get_object_or_404(
            OrganisationSubscription.objects.select_related("plan"),
            organisation=organisation,
        )

    def perform_update(self, serializer):
        with transaction.atomic():
            subscription = self.get_object()

            auto_renew = serializer.validated_data.get(
                "auto_renew",
                subscription.auto_renew,
            )

            subscription.auto_renew = auto_renew
            subscription.save(update_fields=["auto_renew"])


class SubscriptionPermissionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        organisation = request.user.get_organisation()

        if not organisation:
            return Response(
                {"detail": "Organisation not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        subscription = (
            OrganisationSubscription.objects.filter(organisation=organisation)
            .select_related("plan")
            .first()
        )

        if not subscription:
            return Response(
                {"detail": "No subscription found for this organisation."},
                status=status.HTTP_404_NOT_FOUND,
            )

        current_property_count = Property.objects.filter(
            organisation=organisation
        ).count()

        max_properties = subscription.plan.max_properties

        can_create_property = current_property_count < max_properties

        return Response(
            {
                "can_create_property": can_create_property,
                "property_count": current_property_count,
                "max_properties": max_properties,
            },
            status=status.HTTP_200_OK,
        )
