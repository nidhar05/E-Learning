from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView
from django.shortcuts import get_object_or_404

from courses.models import Course
from notifications.models import Notification

from .models import Enrollment
from .serializers import EnrollmentSerializer

class EnrollView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, course_id):
        if request.user.role != 'student':
            return Response({"error": "Only students can enroll"})

        course = get_object_or_404(Course, id=course_id)

        enrollment, created = Enrollment.objects.get_or_create(
            student=request.user,
            course=course
        )

        if not created:
            return Response({"message": "Already enrolled"})

        Notification.objects.create(
            receiver=course.instructor,
            sender=request.user,
            notification_type=Notification.TYPE_ENROLLMENT,
            message=f"{request.user.username} enrolled in your course: {course.title}",
            course=course,
        )

        return Response({"message": "Enrolled successfully"})
     
class EnrollDetailView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EnrollmentSerializer

    def get_queryset(self):
        return Enrollment.objects.filter(student=self.request.user)

