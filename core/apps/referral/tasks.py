from celery import shared_task
from apps.referral.utils import send_referral_invite_email


@shared_task
def send_referral_invite_email_task(referral_id: int):
    from apps.referral.models import Referral

    try:
        referral = Referral.objects.select_related("ambassador__user").get(
            id=referral_id
        )
    except Referral.DoesNotExist:
        return

    send_referral_invite_email(referral)
