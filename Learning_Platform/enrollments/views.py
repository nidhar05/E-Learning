from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q

from courses.models import Course
from notifications.models import Notification

from .models import Enrollment
from .serializers import EnrollmentSerializer

class EnrollView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, course_id):
        if request.user.role != 'student':
            return Response({"error": "Only students can enroll"}, status=status.HTTP_403_FORBIDDEN)

        course = get_object_or_404(Course, id=course_id)
        existing_enrollment = Enrollment.objects.filter(
            student=request.user,
            course=course,
        ).first()

        if existing_enrollment:
            if (
                course.access_type == Course.ACCESS_SUBSCRIPTION
                and not existing_enrollment.payment_verified
            ):
                return Response(
                    {"error": "Subscription payment not verified. Complete payment to enroll."},
                    status=status.HTTP_402_PAYMENT_REQUIRED,
                )
            return Response({"message": "Already enrolled"})

        if course.access_type == Course.ACCESS_SUBSCRIPTION:
            payment_method = request.data.get("payment_method")
            payment_reference = (request.data.get("payment_reference") or "").strip()
            payment_confirmed = bool(request.data.get("payment_confirmed"))

            if payment_method not in {Enrollment.PAYMENT_QR, Enrollment.PAYMENT_CARD}:
                return Response(
                    {"error": "Choose a valid payment method for subscription enrollment."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not payment_confirmed:
                return Response(
                    {"error": "Please confirm that payment is completed."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if len(payment_reference) < 6:
                return Response(
                    {"error": "Enter a valid payment reference (minimum 6 characters)."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            enrollment = Enrollment.objects.create(
                student=request.user,
                course=course,
                payment_method=payment_method,
                payment_reference=payment_reference,
                payment_verified=True,
            )
        else:
            enrollment = Enrollment.objects.create(
                student=request.user,
                course=course,
                payment_verified=True,
            )

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
        return Enrollment.objects.filter(student=self.request.user).filter(
            Q(course__access_type=Course.ACCESS_FREE)
            | Q(course__access_type=Course.ACCESS_SUBSCRIPTION, payment_verified=True)
        )

