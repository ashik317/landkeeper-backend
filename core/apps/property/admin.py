from django.contrib import admin

from .models import (
    Property,
    Mortgage,
    Tenant,
    ComplianceAndCertification,
    UploadDocument,
)


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = (
        "property_name",
        "organisation",
        "property_type",
        "status",
        "address",
        "created_at",
    )


@admin.register(Mortgage)
class MortgageAdmin(admin.ModelAdmin):
    list_display = (
        "lender_name",
        "property",
        "organisation",
        "outstanding_balance",
        "created_at",
    )


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "property",
        "organisation",
        "email",
        "phone",
        "is_active",
        "created_at",
    )


@admin.register(ComplianceAndCertification)
class ComplianceAndCertificationAdmin(admin.ModelAdmin):
    list_display = (
        "certificate_type",
        "property",
        "organisation",
        "certificate_number",
        "expiry_date",
        "created_at",
    )


@admin.register(UploadDocument)
class UploadDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "document_name",
        "property",
        "organisation",
        "document_category",
        "created_at",
    )