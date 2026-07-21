import gocardless_pro
from django.conf import settings

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