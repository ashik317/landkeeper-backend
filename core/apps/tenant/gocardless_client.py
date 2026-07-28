import logging
import uuid
import gocardless_pro
from django.conf import settings

logger = logging.getLogger("apps.tenant.payments")
client = gocardless_pro.Client(
    access_token=settings.GOCARDLESS_ACCESS_TOKEN,
    environment=settings.GOCARDLESS_ENVIRONMENT,
)


def create_redirect_flow(tenant, session_token, success_redirect_url):
    return client.redirect_flows.create(params={
        "description": f"Rent Direct Debit - {tenant}",
        "session_token": session_token,
        "success_redirect_url": success_redirect_url,
        "prefilled_customer": {
            "email": getattr(tenant, "email", None),
        },
    })


def complete_redirect_flow(redirect_flow_id, session_token):
    return client.redirect_flows.complete(
        redirect_flow_id, params={"session_token": session_token}
    )


def create_payment(mandate_id, amount, currency="GBP", idempotency_key=None, metadata=None):
    idempotency_key = idempotency_key or str(uuid.uuid4())
    try:
        return client.payments.create(
            params={
                "amount": int(round(amount * 100)),
                "currency": currency,
                "links": {"mandate": mandate_id},
                "metadata": metadata or {},
            },
            headers={"Idempotency-Key": idempotency_key},
        )
    except gocardless_pro.errors.GoCardlessProError:
        logger.exception(
            "GoCardless create_payment failed",
            extra={"mandate_id": mandate_id, "idempotency_key": idempotency_key},
        )
        raise


def cancel_mandate(mandate_id):
    try:
        return client.mandates.cancel(mandate_id)
    except gocardless_pro.errors.InvalidStateError:
        logger.warning("GoCardless mandate already inactive on cancel: %s", mandate_id)
        return None
    except gocardless_pro.errors.GoCardlessProError:
        logger.exception("GoCardless cancel_mandate failed", extra={"mandate_id": mandate_id})
        raise