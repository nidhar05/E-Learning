from rest_framework.response import Response

from rest_framework.generics import ListAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated

from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(ListAPIView):

    permission_classes = [IsAuthenticated]

    serializer_class = NotificationSerializer

    def get_queryset(self):

        return Notification.objects.filter(
            receiver=self.request.user
        ).order_by("-created_at")


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