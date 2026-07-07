def support_ticket_upload_path(instance, filename):
    if instance.ticket_id:
        return f"support_ticket/{instance.ticket_id}/{filename}"

    if instance.comment_id:
        ticket_id = instance.comment.ticket_id
        if ticket_id:
            return f"support_ticket/{ticket_id}/comments/{instance.comment_id}/{filename}"
        return f"support_ticket/unassigned/comments/{instance.comment_id}/{filename}"

    return f"support_ticket/unassigned/{filename}"