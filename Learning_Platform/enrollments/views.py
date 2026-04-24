from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.conf import settings
from django.utils import timezone
from decimal import Decimal, InvalidOperation

from courses.models import Course
from notifications.models import Notification

from .models import Enrollment
from .serializers import EnrollmentSerializer


def _get_razorpay_client():
    key_id = getattr(settings, "RAZORPAY_KEY_ID", "") or ""
    key_secret = getattr(settings, "RAZORPAY_KEY_SECRET", "") or ""
    if not key_id or not key_secret:
        return None, None, "Payment gateway is not configured."

    try:
        import razorpay
    except ImportError:
        return None, None, "Razorpay SDK is not installed on the server."

    return razorpay.Client(auth=(key_id, key_secret)), key_id, None


def _create_enrollment_notification(user, course):
    message = f"{user.username} enrolled in your course: {course.title}"
    if Notification.objects.filter(
        receiver=course.instructor,
        sender=user,
        notification_type=Notification.TYPE_ENROLLMENT,
        course=course,
        message=message,
    ).exists():
        return

    Notification.objects.create(
        receiver=course.instructor,
        sender=user,
        notification_type=Notification.TYPE_ENROLLMENT,
        message=message,
        course=course,
    )


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
                    {"error": "Complete payment and submit UTR (QR) or verify via gateway (Card)."},
                    status=status.HTTP_402_PAYMENT_REQUIRED,
                )
            return Response({"message": "Already enrolled"})

        if course.access_type == Course.ACCESS_SUBSCRIPTION:
            payment_method = request.data.get("payment_method")
            payment_reference = (request.data.get("payment_reference") or "").strip()
            payment_confirmed = bool(request.data.get("payment_confirmed"))

            if payment_method == Enrollment.PAYMENT_QR:
                if not payment_confirmed:
                    return Response(
                        {"error": "Please confirm QR payment completion."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if len(payment_reference) < 6:
                    return Response(
                        {"error": "Enter a valid UTR / transaction reference (minimum 6 characters)."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                Enrollment.objects.create(
                    student=request.user,
                    course=course,
                    payment_method=Enrollment.PAYMENT_QR,
                    payment_reference=payment_reference,
                    payment_verified=True,
                )
            else:
                return Response(
                    {"error": "Subscription course requires payment. Use QR (with UTR) or card gateway."},
                    status=status.HTTP_402_PAYMENT_REQUIRED,
                )
        else:
            Enrollment.objects.create(
                student=request.user,
                course=course,
                payment_verified=True,
            )

        _create_enrollment_notification(request.user, course)

        return Response({"message": "Enrolled successfully"})


class SubscriptionPaymentOrderCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, course_id):
        if request.user.role != "student":
            return Response({"error": "Only students can pay for enrollment."}, status=status.HTTP_403_FORBIDDEN)

        course = get_object_or_404(Course, id=course_id)
        if course.access_type != Course.ACCESS_SUBSCRIPTION:
            return Response({"error": "Payment order is only for subscription courses."}, status=status.HTTP_400_BAD_REQUEST)

        amount = getattr(course, "amount", None)
        try:
            amount = Decimal(str(amount)) if amount is not None else None
        except (InvalidOperation, TypeError):
            amount = None

        if amount is None or amount <= 0:
            return Response({"error": "Subscription amount is not configured."}, status=status.HTTP_400_BAD_REQUEST)

        existing_enrollment = Enrollment.objects.filter(student=request.user, course=course).first()
        if existing_enrollment and existing_enrollment.payment_verified:
            return Response({"message": "Already enrolled"}, status=status.HTTP_200_OK)

        payment_method = request.data.get("payment_method")
        if payment_method not in {Enrollment.PAYMENT_QR, Enrollment.PAYMENT_CARD}:
            return Response(
                {"error": "Choose a valid payment method (qr or card)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        client, key_id, config_error = _get_razorpay_client()
        if config_error:
            return Response({"error": config_error}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        amount_paise = int(amount * 100)
        receipt = f"c{course.id}-u{request.user.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"[:40]
        order_data = {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": receipt,
            "notes": {
                "course_id": str(course.id),
                "student_id": str(request.user.id),
                "payment_method": payment_method,
            },
        }
        order = client.order.create(data=order_data)

        if existing_enrollment:
            existing_enrollment.payment_method = payment_method
            existing_enrollment.payment_reference = order.get("id")
            existing_enrollment.payment_verified = False
            existing_enrollment.save(update_fields=["payment_method", "payment_reference", "payment_verified"])
        else:
            Enrollment.objects.create(
                student=request.user,
                course=course,
                payment_method=payment_method,
                payment_reference=order.get("id"),
                payment_verified=False,
            )

        return Response(
            {
                "order_id": order.get("id"),
                "amount": amount_paise,
                "currency": "INR",
                "course_title": course.title,
                "razorpay_key_id": key_id,
                "student_name": request.user.username,
            },
            status=status.HTTP_200_OK,
        )


class SubscriptionPaymentVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, course_id):
        if request.user.role != "student":
            return Response({"error": "Only students can verify payment."}, status=status.HTTP_403_FORBIDDEN)

        course = get_object_or_404(Course, id=course_id)
        if course.access_type != Course.ACCESS_SUBSCRIPTION:
            return Response({"error": "Payment verification is only for subscription courses."}, status=status.HTTP_400_BAD_REQUEST)

        razorpay_order_id = (request.data.get("razorpay_order_id") or "").strip()
        razorpay_payment_id = (request.data.get("razorpay_payment_id") or "").strip()
        razorpay_signature = (request.data.get("razorpay_signature") or "").strip()
        payment_method = request.data.get("payment_method")

        if not razorpay_order_id or not razorpay_payment_id or not razorpay_signature:
            return Response(
                {"error": "Missing payment verification fields."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        client, _key_id, config_error = _get_razorpay_client()
        if config_error:
            return Response({"error": config_error}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            client.utility.verify_payment_signature(
                {
                    "razorpay_order_id": razorpay_order_id,
                    "razorpay_payment_id": razorpay_payment_id,
                    "razorpay_signature": razorpay_signature,
                }
            )
        except Exception:
            return Response({"error": "Payment signature verification failed."}, status=status.HTTP_400_BAD_REQUEST)

        enrollment = Enrollment.objects.filter(
            student=request.user,
            course=course,
        ).first()

        if enrollment is None:
            enrollment = Enrollment.objects.create(
                student=request.user,
                course=course,
                payment_method=payment_method if payment_method in {Enrollment.PAYMENT_QR, Enrollment.PAYMENT_CARD} else None,
                payment_reference=razorpay_payment_id,
                payment_verified=True,
            )
        else:
            update_fields = ["payment_reference", "payment_verified"]
            enrollment.payment_reference = razorpay_payment_id
            enrollment.payment_verified = True
            if payment_method in {Enrollment.PAYMENT_QR, Enrollment.PAYMENT_CARD}:
                enrollment.payment_method = payment_method
                update_fields.append("payment_method")
            enrollment.save(update_fields=update_fields)

        _create_enrollment_notification(request.user, course)

        return Response({"message": "Payment verified and enrollment completed."}, status=status.HTTP_200_OK)


class EnrollDetailView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EnrollmentSerializer

    def get_queryset(self):
        return Enrollment.objects.filter(student=self.request.user).filter(
            Q(course__access_type=Course.ACCESS_FREE)
            | Q(course__access_type=Course.ACCESS_SUBSCRIPTION, payment_verified=True)
        )

