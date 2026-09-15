from apps.organisation.models import Organisation, OrganisationSubscription
from apps.subscription.models import PaymentTransaction, PaymentCard
import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

org = Organisation.objects.get(id=82)

# Cancel the old Stripe subscription so it's not left dangling
old_sub = getattr(org, "subscription", None)
if old_sub and old_sub.stripe_subscription_id:
    try:
        stripe.Subscription.cancel(old_sub.stripe_subscription_id)
    except stripe.error.InvalidRequestError:
        pass

PaymentTransaction.objects.filter(organisation=org).delete()
PaymentCard.objects.filter(organisation=org).delete()
OrganisationSubscription.objects.filter(organisation=org).delete()

org.has_used_trial = False
org.stripe_customer_id = None  # force a fresh Stripe customer too
org.save(update_fields=["has_used_trial", "stripe_customer_id"])

print("Reset complete for org:", org.id)
print("has_used_trial:", org.has_used_trial)
