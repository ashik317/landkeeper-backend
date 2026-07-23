from django.db import models
from django.utils.translation import gettext_lazy as _


class PropertyType(models.TextChoices):
    HOUSE = "HOUSE", _("House")
    FLAT = "FLAT", _("Flat")
    MAISONETTE = "MAISONETTE", _("Maisonette")
    BUNGALOW = "BUNGALOW", _("Bungalow")
    RESIDENTIAL = "RESIDENTIAL", _("Residential")
    HMO = "HMO", _("HMO")
    COMMERCIAL = "COMMERCIAL", _("Commercial")
    HOLIDAY_LET = "HOLIDAY_LET", _("Holiday Let")


class PropertyOwnerType(models.TextChoices):
    OWNER = "OWNER", _("Owner")
    COMPANY = "COMPANY", _("Company")

class StatusType(models.TextChoices):
    OCCUPIED = "OCCUPIED", _("Occupied")
    VACANT = "VACANT", _("Vacant")
    UNDER_MAINTENANCE = "UNDER_MAINTENANCE", _("Under Maintenance")


class CertificateType(models.TextChoices):
    GAS_SAFETY_CERTIFICATE = "GAS_SAFETY_CERTIFICATE", _("Gas Safety Certificate")
    EPC_CERTIFICATE = "EPC_CERTIFICATE", _("EPC Certificate")
    ELECTRICAL_SAFETY_CERTIFICATE = "ELECTRICAL_SAFETY_CERTIFICATE", _(
        "Electrical Safety Certificate"
    )
    FIRE_RISK_ASSESSMENT = "FIRE_RISK_ASSESSMENT", _("Fire Risk Assessment")
    HMO_LICENCE = "HMO_LICENCE", _("HMO Licence")
    PAT_TESTING = "PAT_TESTING", _("PAT Testing")
    LEGIONELLA_ASSESSMENT = "LEGIONELLA_ASSESSMENT", _("Legionella Assessment")
    INSURANCE_DOCUMENT = "INSURANCE_DOCUMENT", _("Insurance Document")


class ProductType(models.TextChoices):
    FIXED_RATE = "FIXED_RATE", _("Fixed Rate")
    VARIABLE_RATE = "VARIABLE_RATE", _("Variable Rate")
    TRACKER = "TRACKER", _("Tracker")
    OFFSET = "OFFSET", _("Offset")


class MortgageProductType(models.TextChoices):
    FIXED_RATE = "FIXED_RATE", _("Fixed Rate")
    VARIABLE_RATE = "VARIABLE_RATE", _("Variable Rate")
    TRACKER = "TRACKER", _("Tracker")
    OFFSET = "OFFSET", _("Offset")


class DocumentCategoryType(models.TextChoices):
    MORTGAGE_DOCUMENTS = "MORTGAGE_DOCUMENTS", _("Mortgage Documents")
    TENANCY_AGREEMENT = "TENANCY_AGREEMENT", _("Tenancy Agreement")
    CERTIFICATE = "CERTIFICATE", _("Certificate")
    INSURANCE = "INSURANCE", _("Insurance")
    INVOICE = "INVOICE", _("Invoice")
    TAX_DOCUMENT = "TAX_DOCUMENT", _("Tax Document")
    PROPERTY_PHOTO = "PROPERTY_PHOTO", _("Property Photo")
    LEGAL_DOCUMENT = "LEGAL_DOCUMENT", _("Legal Document")


class TransactionType(models.TextChoices):
    INCOME = "INCOME", _("Income")
    EXPENSE = "EXPENSE", _("Expense")


class Category(models.TextChoices):
    RENTAL_INCOME = "RENTAL_INCOME", _("Rental Income")
    MORTGAGE_PAYMENT = "MORTGAGE_PAYMENT", _("Mortgage Payment")
    REPAIRS = "REPAIRS", _("Repairs")
    INSURANCE = "INSURANCE", _("Insurance")
    SERVICE_CHARGES = "SERVICE_CHARGES", _("Service Charges")
    UTILITIES = "UTILITIES", _("Utilities")
    MANAGEMENT_FEES = "MANAGEMENT_FEES", _("Management Fees")
    TAX = "TAX", _("Tax")
    OTHER = "OTHER", _("Other")

class PropertyTenureType(models.TextChoices):
    FREEHOLD = "FREEHOLD", _("Freehold")
    LEASEHOLD = "LEASEHOLD", _("Leasehold")