from django.contrib import admin

from .models import Organisation, OrganisationUser


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "updated_at")


@admin.register(OrganisationUser)
class OrganisationUserAdmin(admin.ModelAdmin):
    list_display = ("user", "organisation", "role", "created_at", "updated_at")
    list_filter = ("role", "organisation")
    search_fields = (
        "user__email",
        "organisation__name",
    )