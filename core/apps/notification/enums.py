from django.db import models
from django.utils.translation import gettext_lazy as _


class NotificationType(models.TextChoices):
    NEW_SUPPORT_TICKET = "NEW_SUPPORT_TICKET", _("New Support Ticket")
    NEW_TICKET_COMMENT = "NEW_TICKET_COMMENT", _("New Ticket Comment")
    TICKET_STATUS_CHANGED = "TICKET_STATUS_CHANGED", _("Ticket Status Changed")
    NEW_MAINTENANCE_REQUEST = "NEW_MAINTENANCE_REQUEST", _("New Maintenance Request")
    MAINTENANCE_STATUS_CHANGED = "MAINTENANCE_STATUS_CHANGED", _("Maintenance Status Changed")