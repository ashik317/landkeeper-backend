from django.db import models


class PlanType(models.TextChoices):
    BASIC = "BASIC", "Basic"
    STANDARD = "STANDARD", "Standard"
    PREMIUM = "PREMIUM", "Premium"
