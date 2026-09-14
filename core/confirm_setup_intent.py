import stripe
from django.conf import settings
from apps.organisation.models import OrganisationSubscription

stripe.api_key = settings.STRIPE_SECRET_KEY

# The client_secret you got back — extract the setup intent ID from it
client_secret = "seti_1UFY59RbskrYvpYHu1NXrqdj_secret_VG4DuUpHEk8iUqgkW4QOlonx8Ph4Gwk"
setup_intent_id = client_secret.split("_secret_")[0]

# Attach a Stripe TEST payment method (this only works in test mode)
sub = OrganisationSubscription.objects.get(alias="05a42f9a-f8f8-47a8-99a4-1f7784ae1063")
stripe_subscription = stripe.Subscription.retrieve(sub.stripe_subscription_id)
customer_id = stripe_subscription.customer

pm = stripe.PaymentMethod.create(
    type="card",
    card={"token": "tok_visa"},  # Stripe's built-in test token
)
stripe.PaymentMethod.attach(pm.id, customer=customer_id)

confirmed = stripe.SetupIntent.confirm(
    setup_intent_id,
    payment_method=pm.id,
)

print("SetupIntent status:", confirmed.status)

if confirmed.status == "succeeded":
    stripe.Subscription.modify(
        stripe_subscription.id,
        default_payment_method=pm.id,
    )
    print("Attached payment method as default on subscription.")
