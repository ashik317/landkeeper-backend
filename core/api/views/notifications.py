from django.utils import timezone
from rest_framework import generics, status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.notification.models import Notification
from api.serializers.notifications import NotificationSerializer


class NotificationListAPIView(ListAPIView):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)


class NotificationDetailAPIView(RetrieveAPIView):
    serializer_class = NotificationSerializer
    lookup_field = "id"

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)


class NotificationUnreadCountAPIView(APIView):
    def get(self, request):
        count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return Response({"unread_count": count})


class NotificationMarkAsReadAPIView(APIView):
    def post(self, request, id):
        notification = generics.get_object_or_404(
            Notification, id=id, recipient=request.user
        )
        notification.mark_as_read()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificationMarkAllAsReadAPIView(APIView):
    def post(self, request):
        updated = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).update(is_read=True, read_at=timezone.now())
        return Response({"updated": updated})