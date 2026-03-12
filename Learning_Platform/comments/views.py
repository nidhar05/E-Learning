from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import status

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

        text = self.request.data.get("text", "").strip()
        if len(text) < 3:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"text": "Comment must be at least 3 characters long."})

        comment = serializer.save(user=user)

        if comment.parent:
            Notification.objects.create(
                receiver=comment.parent.user,
                sender=user,
                message=f"{user.username} replied to your comment"
            )
        else:
            # Top-level comment: Notify the instructor
            if user != course.instructor:
                Notification.objects.create(
                    receiver=course.instructor,
                    sender=user,
                    message=f"{user.username} commented on your course: {course.title}"
                )


class CommentDeleteView(generics.DestroyAPIView):
    """Allow users to delete their own comments."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Comment.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        try:
            comment = self.get_queryset().get(pk=kwargs["pk"])
        except Comment.DoesNotExist:
            return Response(
                {"error": "Comment not found or you don't have permission to delete it."},
                status=status.HTTP_404_NOT_FOUND
            )
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)