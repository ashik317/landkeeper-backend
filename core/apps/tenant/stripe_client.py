import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_payment_intent(amount, currency="gbp", customer_id=None, payment_method_id=None):
    params = {
        "amount": int(amount * 100),
        "currency": currency,
        "confirm": payment_method_id is not None,
        "automatic_payment_methods": {
            "enabled": True,
            "allow_redirects": "never",
        },
    }
    if customer_id:
        params["customer"] = customer_id
    if payment_method_id:
        params["payment_method"] = payment_method_id
    return stripe.PaymentIntent.create(**params)