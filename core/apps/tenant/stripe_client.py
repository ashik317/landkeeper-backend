import logging

import stripe
from django.conf import settings

logger = logging.getLogger("apps.tenant.payments")

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_payment_intent(
    amount,
    currency="gbp",
    customer_id=None,
    payment_method_id=None,
    idempotency_key=None,
    metadata=None,
    stripe_account_destination=None,
    application_fee_amount=None,
):
    params = {
        "amount": int(round(amount * 100)),
        "currency": currency,
        "confirm": payment_method_id is not None,
        "metadata": metadata or {},
    }

    if payment_method_id:
        params["payment_method_types"] = ["card"]
    else:
        params["automatic_payment_methods"] = {
            "enabled": True,
            "allow_redirects": "never",
        }

    if customer_id:
        params["customer"] = customer_id
    if payment_method_id:
        params["payment_method"] = payment_method_id

    if stripe_account_destination:
        params["transfer_data"] = {"destination": stripe_account_destination}
        if application_fee_amount:
            params["application_fee_amount"] = int(application_fee_amount)

    request_options = {}
    if idempotency_key:
        request_options["idempotency_key"] = idempotency_key

    try:
        return stripe.PaymentIntent.create(**params, **request_options)
    except stripe.error.CardError:
        logger.info("Stripe card declined", extra={"idempotency_key": idempotency_key})
        raise
    except stripe.error.StripeError:
        logger.exception(
            "Stripe create_payment_intent failed",
            extra={"idempotency_key": idempotency_key},
        )
        raise


def handle_tenant_payment_succeeded(payment_intent):
    from apps.tenant.models import CardPayment, PaymentMethod
    from apps.tenant.enums import (
        RentPaymentStatusChoices,
        PaymentProviderChoices,
        PaymentMethodTypeChoices,
        PaymentMethodStatusChoices,
    )

    provider_payment_id = getattr(payment_intent, "id", None)
    if not provider_payment_id:
        return

    try:
        card_payment = CardPayment.objects.get(provider_payment_id=provider_payment_id)
    except CardPayment.DoesNotExist:
        logger.warning(
            "Tenant webhook: payment_intent.succeeded for unknown CardPayment",
            extra={"provider_payment_id": provider_payment_id},
        )
        return

    card_payment.status = RentPaymentStatusChoices.CLEARED
    update_fields = ["status"]

    if not card_payment.payment_method_id:
        pm_id = getattr(payment_intent, "payment_method", None)
        if pm_id:
            pm_id_str = pm_id if isinstance(pm_id, str) else getattr(pm_id, "id", None)
            if pm_id_str:
                existing_pm = PaymentMethod.objects.filter(
                    tenant=card_payment.tenant,
                    provider=PaymentProviderChoices.STRIPE,
                    provider_payment_method_id=pm_id_str,
                ).first()

                if existing_pm:
                    card_payment.payment_method = existing_pm
                else:
                    try:
                        stripe_pm = stripe.PaymentMethod.retrieve(pm_id_str)
                        card = getattr(stripe_pm, "card", None)
                        new_pm = PaymentMethod.objects.create(
                            tenant=card_payment.tenant,
                            provider=PaymentProviderChoices.STRIPE,
                            method_type=PaymentMethodTypeChoices.CARD,
                            provider_payment_method_id=pm_id_str,
                            status=PaymentMethodStatusChoices.ACTIVE,
                            is_default=False,
                            card_last4=getattr(card, "last4", None) if card else None,
                            card_brand=getattr(card, "brand", None) if card else None,
                            card_exp_month=getattr(card, "exp_month", None) if card else None,
                            card_exp_year=getattr(card, "exp_year", None) if card else None,
                        )
                        card_payment.payment_method = new_pm
                    except stripe.error.StripeError:
                        logger.exception(
                            "Failed to fetch/create PaymentMethod during webhook backfill",
                            extra={"payment_method_id": pm_id_str},
                        )

        update_fields.append("payment_method")

    card_payment.save(update_fields=update_fields)


def handle_tenant_payment_failed(payment_intent):
    from apps.tenant.models import CardPayment
    from apps.tenant.enums import RentPaymentStatusChoices

    provider_payment_id = getattr(payment_intent, "id", None)
    if not provider_payment_id:
        return

    try:
        card_payment = CardPayment.objects.get(provider_payment_id=provider_payment_id)
    except CardPayment.DoesNotExist:
        logger.warning(
            "Tenant webhook: payment_intent.payment_failed for unknown CardPayment",
            extra={"provider_payment_id": provider_payment_id},
        )
        return

    last_payment_error = getattr(payment_intent, "last_payment_error", None)
    failure_message = (
        getattr(last_payment_error, "message", None) if last_payment_error else None
    ) or "Payment failed."

    card_payment.status = RentPaymentStatusChoices.FAILED
    card_payment.failure_reason = failure_message
    card_payment.save(update_fields=["status", "failure_reason"])