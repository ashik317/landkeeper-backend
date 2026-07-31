from django.db import models
from django.contrib.auth import get_user_model
from apps.organisation.models import Organisation
from common.models import CreatedAtUpdatedAtBaseModel, DocumentFile

User = get_user_model()

class Document(CreatedAtUpdatedAtBaseModel):
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=64)

    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, related_name="documents"
    )
    uploaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="uploaded_documents"
    )
    file = models.OneToOneField(
        DocumentFile, on_delete=models.CASCADE, related_name="document"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title