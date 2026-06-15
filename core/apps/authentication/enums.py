from django.db import models
from django.utils.translation import gettext_lazy as _

class NameTitleChoices(models.TextChoices):
    MR = "MR", _("Mr.")
    MRS = "MRS", _("Mrs.")
    MS = "MS", _("Ms.")
    DR = "DR", _("Dr.")
    MISS = "MISS", _("Miss.")
    MADAM = "MADAM", _("Madam.")
    MAIDEN = "MAIDEN", _("Maiden.")
    PROFESSOR = "PROFESSOR", _("Professor.")
    DOCTOR = "DOCTOR", _("Doctor.")

class UserRoleChoices(models.TextChoices):
    LANDLORD = "LANDLORD", _("Landlord")
    MORTGAGE_ADVISER = "MORTGAGE_ADVISER", _("Mortgage Adviser")
    ACCOUNTANT = "ACCOUNTANT", _("Accountant")
    LETTING_AGENT = "LETTING_AGENT", _("Letting Agent")
    ADMIN = "ADMIN", _("Admin")