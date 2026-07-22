import uuid
from django.db import models

from apps.organisation.models import Organisation
from apps.property.models import Tenant, Property
from apps.tenant.enums import (
    PaymentProviderChoices,
    PaymentMethodTypeChoices,
    PaymentMethodStatusChoices,
    RentPaymentStatusChoices
)
from apps.tenant.utils import receipt_upload_path
from common.models import CreatedAtUpdatedAtBaseModel


class PaymentMethod(CreatedAtUpdatedAtBaseModel):
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="payment_methods"
    )
    provider = models.CharField(max_length=20, choices=PaymentProviderChoices.choices)
    method_type = models.CharField(
        max_length=20, choices=PaymentMethodTypeChoices.choices
    )
    provider_customer_id = models.CharField(max_length=128, blank=True, null=True)
    provider_mandate_id = models.CharField(max_length=128, blank=True, null=True)  # GoCardless
    provider_payment_method_id = models.CharField(
        max_length=128, blank=True, null=True
    )

    status = models.CharField(
        max_length=20,
        choices=PaymentMethodStatusChoices.choices,
        default=PaymentMethodStatusChoices.PENDING,
    )
    is_default = models.BooleanField(default=True)
    card_last4 = models.CharField(max_length=4, blank=True, null=True)
    card_brand = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.tenant} - {self.get_method_type_display()} ({self.status})"


class RentPayment(CreatedAtUpdatedAtBaseModel):
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="rent_payments"
    )
    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="property_rent_payments"
    )
    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, related_name="organisation_rent_payments"
    )
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rent_payments",
    )
    reference = models.CharField(max_length=64, unique=True, editable=False, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    paid_date = models.DateField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=RentPaymentStatusChoices.choices,
        default=RentPaymentStatusChoices.PENDING,
    )
    provider_payment_id = models.CharField(max_length=128, blank=True, null=True)
    receipt_file = models.FileField(
        upload_to=receipt_upload_path, blank=True, null=True
    )
    failure_reason = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-due_date"]
        indexes = [
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["tenant", "due_date"]),
        ]

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"RENT-{self.due_date:%Y%m}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference} - {self.tenant} - £{self.amount}"


class ProcessedWebhookEvent(models.Model):
    provider = models.CharField(max_length=20)
    event_id = models.CharField(max_length=128)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "event_id"], name="unique_provider_event"
            )
        ]
        indexes = [
            models.Index(fields=["provider", "event_id"]),
        ]
