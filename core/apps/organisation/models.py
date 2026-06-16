from common.models import (
    NameSlugDescriptionBaseModel,
    TimestampThumbnailImageField
)
from django.db import models

class Organisation(NameSlugDescriptionBaseModel):
    email = models.EmailField(unique=True)
    logo = TimestampThumbnailImageField(
        upload_to="organization/logo", blank=True, null=True
    )
    profile_image = TimestampThumbnailImageField(
        upload_to="organization/profile", blank=True, null=True
    )
    primary_mobile = models.CharField(max_length=20)
    other_contact = models.CharField(max_length=64, blank=True, null=True)
    contact_person = models.CharField(max_length=64, blank=True, null=True)
    contact_person_designation = models.CharField(max_length=64, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at", "-updated_at"]

    def __str__(self):
        return f"{self.email} - {self.name}"