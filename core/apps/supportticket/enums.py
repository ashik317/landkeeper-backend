from django.db import models
from django.utils.translation import gettext_lazy as _


class SupportTicketType(models.TextChoices):
    BUG_REPORT = "BUG_REPORT", _("Bug Report")
    FEEDBACK = "FEEDBACK", _("Feedback")
    FEATURE_REQUEST = "FEATURE_REQUEST", _("Feature Request")


class SupportTicketStatus(models.TextChoices):
    OPEN = "OPEN", _("Open")  # user created
    IN_PROGRESS = "IN_PROGRESS", _("In Progress")  # actively working
    COMPLETED = "COMPLETED", _("Completed")  # dev work done, not deployed
    RESOLVED = "RESOLVED", _("Resolved")  # deployed & confirmed
    CLOSED = "CLOSED", _("Closed")  # closed by user or support team


class SupportTicketPriority(models.TextChoices):
    URGENT = "URGENT", _("Urgent")
    MEDIUM = "MEDIUM", _("Medium")
    NORMAL = "NORMAL", _("Normal")
    WHEN_POSSIBLE = "WHEN_POSSIBLE", _("When Possible")
