from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from notifications.models import Notification

from .models import Comment
from .serializers import CommentSerializer
from enrollments.models import Enrollment
from courses.models import Course


class CommentListCreateView(generics.ListCreateAPIView):

    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        course_id = self.request.query_params.get("course")

        return Comment.objects.filter(
            course_id=course_id,
            parent=None
        ).order_by("-created_at")


    def perform_create(self, serializer):

        course_id = self.request.data.get("course")

        course = Course.objects.get(id=course_id)

        user = self.request.user

        enrolled = Enrollment.objects.filter(
            student=user,
            course=course
        ).exists()

        if user != course.instructor and not enrolled:
            raise PermissionDenied("You must enroll in the course")

        comment = serializer.save(user=user)

        if comment.parent:

            Notification.objects.create(

                receiver=comment.parent.user,
                sender=user,

                message=f"{user.username} replied to your comment"

        )