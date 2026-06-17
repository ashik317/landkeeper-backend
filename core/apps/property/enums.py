from django.db import models


class PropertyType(models.TextChoices):
    RESIDENTIAL = "RESIDENTIAL", "Residential"
    HMO = "HMO", "HMO"
    COMMERCIAL = "COMMERCIAL", "Commercial"
    MIXED_USE = "MIXED_USE", "Mixed Use"
    HOLIDAY_LET = "HOLIDAY_LET", "Holiday Let"
