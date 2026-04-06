from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated

from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(ListAPIView):

    permission_classes = [IsAuthenticated]

    serializer_class = NotificationSerializer

    def get_queryset(self):
        status_filter = self.request.query_params.get("status", "unread")

        queryset = Notification.objects.select_related(
            "sender",
            "course",
            "video",
            "comment",
            "comment__parent",
        ).filter(
            receiver=self.request.user,
        )

        if status_filter == "read":
            queryset = queryset.filter(is_read=True)
        elif status_filter != "all":
            queryset = queryset.filter(is_read=False)

        return queryset.order_by("-created_at")


class MarkNotificationReadView(UpdateAPIView):
        
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):

        try:
            notification = Notification.objects.get(
                id=pk,
                receiver=request.user
            )

        except Notification.DoesNotExist:

            return Response({"error": "Notification not found"}, status=404)

        notification.is_read = True
        notification.save()

        return Response({
            "message": "Notification marked as read"
        })


class MarkAllNotificationsReadView(APIView):

    permission_classes = [IsAuthenticated]

    def put(self, request):
        updated_count = Notification.objects.filter(
            receiver=request.user,
            is_read=False
        ).update(is_read=True)

        return Response({
            "message": "Notifications marked as read",
            "updated_count": updated_count
        })
