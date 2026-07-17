import django_filters
from django_filters import BaseInFilter, CharFilter
from .models import SupportTicket


class CharInFilter(BaseInFilter, CharFilter):
    pass


class SupportTicketFilter(django_filters.FilterSet):
    ticket_type = CharInFilter(field_name="ticket_type", lookup_expr="in")
    status = CharInFilter(field_name="status", lookup_expr="in")
    priority = CharInFilter(field_name="priority", lookup_expr="in")
    created_by = CharInFilter(field_name="created_by", lookup_expr="in")

    class Meta:
        model = SupportTicket
        fields = []
