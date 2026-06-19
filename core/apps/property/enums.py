from django.db import models
from django.utils.translation import gettext_lazy as _

class PropertyType(models.TextChoices):
    RESIDENTIAL = "RESIDENTIAL", _("Residential")
    HMO = "HMO", _("HMO")
    COMMERCIAL = "COMMERCIAL", _("Commercial")
    MIXED_USE = "MIXED_USE", _("Mixed Use")
    HOLIDAY_LET = "HOLIDAY_LET", _("Holiday Let")

class CertificateType(models.TextChoices):
    GAS_SAFETY_CERTIFICATE = "GAS_SAFETY_CERTIFICATE", _("Gas Safety Certificate")
    EPC_CERTIFICATE = "EPC_CERTIFICATE", _("EPC Certificate")
    ELECTRICAL_SAFETY_CERTIFICATE = "ELECTRICAL_SAFETY_CERTIFICATE", _("Electrical Safety Certificate")
    FIRE_RISK_ASSESSMENT = "FIRE_RISK_ASSESSMENT", _("Fire Risk Assessment")
    HMO_LICENCE = "HMO_LICENCE", _("HMO Licence")
    PAT_TESTING = "PAT_TESTING", _("PAT Testing")
    LEGIONELLA_ASSESSMENT = "LEGIONELLA_ASSESSMENT", _("Legionella Assessment")
    INSURANCE_DOCUMENT = "INSURANCE_DOCUMENT", _("Insurance Document")