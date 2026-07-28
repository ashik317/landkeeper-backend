from apps.notification import tasks


def notify_ticket_created(ticket):
    tasks.notify_ticket_created_task.delay(ticket_id=ticket.id)


def notify_ticket_status_updated(ticket, updated_by=None):
    tasks.notify_ticket_status_updated_task.delay(
        ticket_id=ticket.id,
        updated_by_id=updated_by.id if updated_by else None,
    )


def notify_new_comment(comment):
    tasks.notify_new_comment_task.delay(comment_id=comment.id)