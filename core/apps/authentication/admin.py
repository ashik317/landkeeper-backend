from django.contrib import admin
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from apps.authentication.models import User, InviteUser, Permission

admin.site.register(InviteUser)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["-created_at"]
    list_display = [
        "id",
        "alias",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_active",
    ]
    search_fields = ["email", "first_name", "last_name"]
    list_filter = ["is_staff", "is_active", "title"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Personal Info"),
            {
                "fields": (
                    "title",
                    "first_name",
                    "middle_name",
                    "last_name",
                    "phone",
                    "profile_image",
                )
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login",)}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )

    USERNAME_FIELD = "email"


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = [
        "alias",
        "user",
        "property",
        "mortgage",
        "can_view",
        "can_edit",
    ]
    search_fields = ["alias", "user__email", "property__name", "mortgage__name"]
    list_filter = ["can_view", "can_edit"]
