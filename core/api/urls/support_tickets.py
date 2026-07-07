from django.urls import path

from api.views.support_tickets import (
    SupportTicketListView,
    SupportTicketDetailView,
    SupportTicketCommentListCreateView,
    SupportTicketCommentDetailView
)

urlpatterns = [
    path(
        "",
        SupportTicketListView.as_view(),
        name="support-ticket",
    ),
    path(
        "/<uuid:ticket_alias>",
        SupportTicketDetailView.as_view(),
        name="support-ticket-detail",
    ),
    path(
        "/<uuid:ticket_alias>/comments",
        SupportTicketCommentListCreateView.as_view(),
        name="support-ticket-comments",
    ),
    path(
        "/<uuid:ticket_alias>/comments/<uuid:comment_alias>",
        SupportTicketCommentDetailView.as_view(),
        name="support-ticket-comment-detail",
    ),
]
