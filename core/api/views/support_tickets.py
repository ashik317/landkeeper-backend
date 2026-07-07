from django.shortcuts import get_object_or_404
from rest_framework.filters import SearchFilter
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated
from apps.supportticket.models import SupportTicket, SupportTicketComment
from ..serializers.support_tickets import (
    SupportTicketSerializer,
    SupportTicketCommentSerializer,
)


class SupportTicketListView(ListCreateAPIView):
    serializer_class = SupportTicketSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = [
        "ticket_id",
        "created_by__email",
        "created_by__phone",
        "created_by__title",
        "created_by__first_name",
        "created_by__middle_name",
        "created_by__last_name",
    ]

    def get_queryset(self):
        user = self.request.user

        qs = (
            SupportTicket.objects.select_related("created_by", "organisation")
            .prefetch_related("files")
            .order_by("-created_at")
        )

        if user.is_superuser:
            organisation_alias = self.request.query_params.get("organisation")
            if organisation_alias:
                qs = qs.filter(organisation__alias=organisation_alias)
            return qs

        # Non-superusers only ever see tickets belonging to their own organisation.
        organisation = user.get_organisation()
        if not organisation:
            return qs.none()

        return qs.filter(organisation=organisation)

    def perform_create(self, serializer):
        user = self.request.user
        organisation = (
            getattr(self.request, "organisation", None)
            if user.is_superuser
            else user.get_organisation()
        )

        serializer.save(
            created_by=user,
            organisation=organisation,
        )


class SupportTicketDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = SupportTicketSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = SupportTicket.objects.select_related("created_by", "organisation")

        if user.is_superuser:
            return qs

        organisation = user.get_organisation()
        if not organisation:
            return qs.none()

        return qs.filter(organisation=organisation)

    def get_object(self):
        ticket_alias = self.kwargs.get("ticket_alias")
        return get_object_or_404(self.get_queryset(), alias=ticket_alias)


class SupportTicketCommentListCreateView(ListCreateAPIView):
    serializer_class = SupportTicketCommentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_ticket(self):
        if not hasattr(self, "_ticket"):
            ticket_qs = SupportTicketDetailView.as_view()
            user = self.request.user
            qs = SupportTicket.objects.all()
            if not user.is_superuser:
                organisation = user.get_organisation()
                qs = qs.filter(organisation=organisation) if organisation else qs.none()
            self._ticket = get_object_or_404(qs, alias=self.kwargs.get("ticket_alias"))
        return self._ticket

    def get_queryset(self):
        ticket = self.get_ticket()
        return (
            SupportTicketComment.objects.filter(ticket=ticket, parent__isnull=True)
            .select_related("author")
            .prefetch_related("replies", "files")
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, ticket=self.get_ticket())


class SupportTicketCommentDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = SupportTicketCommentSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        ticket_alias = self.kwargs.get("ticket_alias")
        comment_alias = self.kwargs.get("comment_alias")

        user = self.request.user
        ticket_qs = SupportTicket.objects.all()
        if not user.is_superuser:
            organisation = user.get_organisation()
            ticket_qs = (
                ticket_qs.filter(organisation=organisation)
                if organisation
                else ticket_qs.none()
            )
        ticket = get_object_or_404(ticket_qs, alias=ticket_alias)

        return get_object_or_404(
            SupportTicketComment,
            alias=comment_alias,
            ticket=ticket,
        )