from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Enrollment
from courses.models import Course
from rest_framework.generics import ListAPIView
from .serializers import EnrollmentSerializer
from django.shortcuts import get_object_or_404

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

        return Response({"message": "Enrolled successfully"})
     
class EnrollDetailView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EnrollmentSerializer

    def get_queryset(self):
        return Enrollment.objects.filter(student=self.request.user)

