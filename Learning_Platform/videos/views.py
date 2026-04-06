from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from enrollments.models import Enrollment
from notifications.models import Notification

from .models import Video
from .serializers import VideoSerializer

class VideoListCreateView(generics.ListCreateAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):

        if self.request.user.role != "instructor":
            raise PermissionDenied("Only instructors can upload videos")

        course = serializer.validated_data["course"]

        if self.request.user != course.instructor:
            raise PermissionDenied("You can only upload videos to your own courses")

        video = serializer.save()

        enrollments = Enrollment.objects.select_related("student").filter(course=course)
        notifications = [
            Notification(
                receiver=enrollment.student,
                sender=self.request.user,
                notification_type=Notification.TYPE_NEW_LESSON,
                message=f"New lesson added to {course.title}: {video.title}",
                course=course,
                video=video,
            )
            for enrollment in enrollments
            if enrollment.student != self.request.user
        ]

        if notifications:
            Notification.objects.bulk_create(notifications)
