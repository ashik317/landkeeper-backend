from django.contrib import admin

from apps.supportticket.models import (
    SupportTicket,
    SupportTicketComment,
    SupportTicketFile,
)


class SupportTicketFileByTicketInline(admin.TabularInline):
    model = SupportTicketFile
    fk_name = "ticket"
    extra = 0
    fields = ["file", "created_at"]
    readonly_fields = ["created_at"]


class SupportTicketFileByCommentInline(admin.TabularInline):
    model = SupportTicketFile
    fk_name = "comment"
    extra = 0
    fields = ["file", "created_at"]
    readonly_fields = ["created_at"]


class SupportTicketCommentInline(admin.TabularInline):
    model = SupportTicketComment
    fk_name = "ticket"
    extra = 0
    fields = ["author", "message", "parent", "created_at"]
    readonly_fields = ["created_at"]
    show_change_link = True


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = [
        "ticket_id",
        "subject",
        "ticket_type",
        "organisation",
        "created_by",
        "created_at",
    ]
    list_filter = ["ticket_type", "organisation", "created_at"]
    search_fields = [
        "ticket_id",
        "subject",
        "description",
        "created_by__email",
        "created_by__first_name",
        "created_by__last_name",
        "organisation__name",
    ]
    readonly_fields = ["alias", "ticket_id", "created_at", "updated_at", "created_by"]
    inlines = [SupportTicketFileByTicketInline, SupportTicketCommentInline]
    ordering = ["-created_at"]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("organisation", "created_by")
        )


@admin.register(SupportTicketComment)
class SupportTicketCommentAdmin(admin.ModelAdmin):
    list_display = ["id", "ticket", "author", "parent", "short_message", "created_at"]
    list_filter = ["created_at"]
    search_fields = [
        "message",
        "author__email",
        "author__first_name",
        "author__last_name",
        "ticket__ticket_id",
    ]
    readonly_fields = ["alias", "created_at", "updated_at", "author"]
    inlines = [SupportTicketFileByCommentInline]
    ordering = ["-created_at"]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("ticket", "author", "parent")
        )

    def short_message(self, obj):
        return obj.message[:75] + ("…" if len(obj.message) > 75 else "")

    short_message.short_description = "Message"


@admin.register(SupportTicketFile)
class SupportTicketFileAdmin(admin.ModelAdmin):
    list_display = ["id", "file", "ticket", "comment", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["ticket__ticket_id", "comment__alias"]
    readonly_fields = ["alias", "created_at", "updated_at"]
    ordering = ["-created_at"]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("ticket", "comment")
        )