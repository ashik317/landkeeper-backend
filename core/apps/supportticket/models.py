from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.organisation.models import Organisation
from apps.supportticket.enums import SupportTicketType
from apps.supportticket.utils import support_ticket_upload_path
from common.models import CreatedAtUpdatedAtBaseModel


class SupportTicket(CreatedAtUpdatedAtBaseModel):
    ticket_type = models.CharField(
        max_length=20,
        choices=SupportTicketType.choices,
        verbose_name=_("Ticket Type"),
    )
    subject = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Subject"),
    )
    description = models.TextField(verbose_name=_("Description"))
    ticket_id = models.CharField(max_length=50, blank=True, unique=True)
    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="support_tickets",
        verbose_name=_("Organisation"),
    )

    class Meta:
        verbose_name = _("Support Ticket")
        verbose_name_plural = _("Support Tickets")
        ordering = ["-created_at", "-updated_at"]

    def __str__(self):
        return f"Support Ticket #{self.id} - {self.subject}"


class SupportTicketComment(CreatedAtUpdatedAtBaseModel):
    message = models.TextField(verbose_name=_("Message"))

    # Fk
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="replies",
        blank=True,
        null=True,
        verbose_name=_("Parent Comment"),
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="support_ticket_comments",
        verbose_name=_("Commented By"),
    )
    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.CASCADE,
        related_name="support_ticket_comments",
        verbose_name=_("Ticket"),
    )

    class Meta:
        verbose_name = _("Support Ticket Comment")
        verbose_name_plural = _("Support Ticket Comments")
        ordering = ["-created_at", "-updated_at"]

    def __str__(self):
        return f"Comment by {self.author.email} on Ticket #{self.ticket.id}"


class SupportTicketFile(CreatedAtUpdatedAtBaseModel):
    file = models.FileField(
        upload_to=support_ticket_upload_path,
    )

    # Fk
    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="files",
        verbose_name=_("Ticket"),
    )
    comment = models.ForeignKey(
        SupportTicketComment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="files",
        verbose_name=_("Comment"),
    )

    class Meta:
        verbose_name = _("Support Ticket File")
        verbose_name_plural = _("Support Ticket Files")

    def clean(self):
        if bool(self.ticket) == bool(self.comment):
            raise ValidationError(
                _("File must be attached to either a ticket or a comment, not both.")
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.ticket:
            return f"File for Ticket {self.ticket.ticket_id}"
        return f"File for Comment #{self.comment.id}"