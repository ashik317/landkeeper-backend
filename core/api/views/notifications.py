from django.utils import timezone
from rest_framework import generics, status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.notification.models import Notification
from api.serializers.notifications import NotificationSerializer
from apps.property.models import Tenant


class NotificationListAPIView(ListAPIView):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        user = self.request.user

        if isinstance(user, Tenant):
            return Notification.objects.filter(
                tenant=user
            )
        return Notification.objects.filter(
            recipient=user
        )

class NotificationDetailAPIView(RetrieveAPIView):
    serializer_class = NotificationSerializer
    lookup_field = "id"

    def get_queryset(self):
        user = self.request.user

        if isinstance(user, Tenant):
            return Notification.objects.filter(
                tenant=user
            )
        return Notification.objects.filter(
            recipient=user
        )


class NotificationUnreadCountAPIView(APIView):
    def get(self, request):
        user = request.user

        if isinstance(user, Tenant):
            count = Notification.objects.filter(
                tenant=user,
                is_read=False,
            ).count()
        else:
            count = Notification.objects.filter(
                recipient=user,
                is_read=False,
            ).count()

        return Response({
            "unread_count": count
        })


class NotificationMarkAsReadAPIView(APIView):
    def post(self, request, id):
        user = request.user

        if isinstance(user, Tenant):
            notification = generics.get_object_or_404(
                Notification,
                id=id,
                tenant=user,
            )
        else:
            notification = generics.get_object_or_404(
                Notification,
                id=id,
                recipient=user,
            )

        notification.mark_as_read()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

class NotificationMarkAllAsReadAPIView(APIView):
    def post(self, request):
        user = request.user

        if isinstance(user, Tenant):
            updated = Notification.objects.filter(
                tenant=user,
                is_read=False,
            ).update(
                is_read=True,
                read_at=timezone.now(),
            )
        else:
            updated = Notification.objects.filter(
                recipient=user,
                is_read=False,
            ).update(
                is_read=True,
                read_at=timezone.now(),
            )

        return Response({
            "updated": updated
        })