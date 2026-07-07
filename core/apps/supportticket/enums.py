from django.db import models
from django.utils.translation import gettext_lazy as _


class SupportTicketType(models.TextChoices):
    BUG_REPORT = "BUG_REPORT", _("Bug Report")
    FEEDBACK = "FEEDBACK", _("Feedback")
    FEATURE_REQUEST = "FEATURE_REQUEST", _("Feature Request")
