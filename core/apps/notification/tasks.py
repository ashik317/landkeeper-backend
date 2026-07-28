import logging
from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.apps import apps
from apps.authentication.models import User
from apps.notification.enums import NotificationType
from apps.notification.models import Notification

logger = logging.getLogger(__name__)


def get_support_admins():
    return User.objects.filter(is_staff=True, is_active=True)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def create_notification_task(
    self,
    recipient_id,
    notification_type,
    message,
    data=None,
    actor_id=None,
):
    try:
        if recipient_id == actor_id:
            return None

        notification = Notification.objects.create(
            recipient_id=recipient_id,
            notification_type=notification_type,
            message=message,
            data=data or {},
            created_by_id=actor_id,
        )

        channel_layer = get_channel_layer()
        if channel_layer is not None:
            async_to_sync(channel_layer.group_send)(
                f"notifications_{recipient_id}",
                {
                    "type": "send_notification",
                    "payload": {
                        "alias": str(notification.alias),
                        "notification_type": notification.notification_type,
                        "message": notification.message,
                        "data": notification.data,
                        "created_at": notification.created_at.isoformat(),
                    },
                },
            )

        return str(notification.alias)
    except Exception as exc:
        logger.exception("Failed to create notification for recipient_id=%s", recipient_id)
        raise self.retry(exc=exc)


@shared_task
def notify_ticket_created_task(ticket_id):
    SupportTicket = apps.get_model("supportticket", "SupportTicket")
    try:
        ticket = SupportTicket.objects.select_related("created_by").get(pk=ticket_id)
    except SupportTicket.DoesNotExist:
        logger.warning("notify_ticket_created_task: ticket %s no longer exists", ticket_id)
        return

    for admin in get_support_admins():
        create_notification_task.delay(
            recipient_id=admin.id,
            notification_type=NotificationType.NEW_SUPPORT_TICKET,
            message=f"New support ticket: {ticket.ticket_id} – {ticket.subject or ''}".strip(" –"),
            data={"type": "SUPPORT_TICKET", "alias": str(ticket.alias)},
            actor_id=ticket.created_by_id,
        )


@shared_task
def notify_ticket_status_updated_task(ticket_id, updated_by_id=None):
    SupportTicket = apps.get_model("supportticket", "SupportTicket")
    try:
        ticket = SupportTicket.objects.select_related("created_by").get(pk=ticket_id)
    except SupportTicket.DoesNotExist:
        logger.warning("notify_ticket_status_updated_task: ticket %s no longer exists", ticket_id)
        return

    if not ticket.created_by_id:
        return

    create_notification_task.delay(
        recipient_id=ticket.created_by_id,
        notification_type=NotificationType.TICKET_STATUS_CHANGED,
        message=f"Ticket {ticket.ticket_id} status changed to {ticket.get_status_display()}",
        data={"type": "SUPPORT_TICKET", "alias": str(ticket.alias)},
        actor_id=updated_by_id or ticket.updated_by_id,
    )


@shared_task
def notify_new_comment_task(comment_id):
    SupportTicketComment = apps.get_model("supportticket", "SupportTicketComment")
    try:
        comment = SupportTicketComment.objects.select_related("ticket", "author").get(pk=comment_id)
    except SupportTicketComment.DoesNotExist:
        logger.warning("notify_new_comment_task: comment %s no longer exists", comment_id)
        return

    ticket = comment.ticket
    recipient_ids = {ticket.created_by_id, *get_support_admins().values_list("id", flat=True)}
    recipient_ids.discard(comment.author_id)
    recipient_ids.discard(None)

    for recipient_id in recipient_ids:
        create_notification_task.delay(
            recipient_id=recipient_id,
            notification_type=NotificationType.NEW_TICKET_COMMENT,
            message=f"{comment.author.get_full_name()} commented on {ticket.ticket_id}: {comment.message[:150]}",
            data={"type": "SUPPORT_TICKET", "alias": str(ticket.alias)},
            actor_id=comment.author_id,
        )


@shared_task
def cleanup_old_notifications(days=30):
    from django.utils import timezone

    cutoff = timezone.now() - timezone.timedelta(days=days)
    deleted_count, _ = Notification.objects.filter(
        is_read=True, read_at__lt=cutoff
    ).delete()
    logger.info("cleanup_old_notifications: deleted %s notifications", deleted_count)
    return deleted_count