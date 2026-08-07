from django.db import models
from django.utils.translation import gettext_lazy as _

class PaymentProviderChoices(models.TextChoices):
    GOCARDLESS = "GOCARDLESS", _("GoCardless")
    STRIPE = "STRIPE", _("Stripe")

class PaymentMethodTypeChoices(models.TextChoices):
    DIRECT_DEBIT = "DIRECT_DEBIT", _("Direct Debit")
    CARD = "CARD", _("Card")

class PaymentMethodStatusChoices(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    ACTIVE = "ACTIVE", _("Active")
    FAILED = "FAILED", _("Failed")
    CANCELLED = "CANCELLED", _("Cancelled")

class RentPaymentStatusChoices(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    PROCESSING = "PROCESSING", _("Processing")
    CLEARED = "CLEARED", _("Cleared")
    FAILED = "FAILED", _("Failed")
    OVERDUE = "OVERDUE", _("Overdue")
    REFUNDED = "REFUNDED", _("Refunded")

class MaintenanceStatus(models.TextChoices):
    SUBMITTED = "SUBMITTED", _("Submitted")
    ASSIGNED = "ASSIGNED", _("Assigned")
    IN_PROGRESS = "IN_PROGRESS", _("In Progress")
    COMPLETED = "COMPLETED", _("Completed")

class MaintenanceCategory(models.TextChoices):
    PLUMBING = "PLUMBING", "Plumbing"
    CARPENTRY_SECURITY = "CARPENTRY_SECURITY", _("Carpentry_Security")
    OTHER = "OTHER", _("Other")
