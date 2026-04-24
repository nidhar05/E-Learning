from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from courses.models import Course
from enrollments.models import Enrollment


User = get_user_model()


class EnrollmentPaymentTests(APITestCase):
    def setUp(self):
        self.instructor = User.objects.create_user(
            username="payment_instructor",
            password="testpass123",
            role="instructor",
        )
        self.student = User.objects.create_user(
            username="payment_student",
            password="testpass123",
            role="student",
        )
        self.free_course = Course.objects.create(
            instructor=self.instructor,
            title="Free Course",
            description="Open course",
            access_type=Course.ACCESS_FREE,
        )
        self.subscription_course = Course.objects.create(
            instructor=self.instructor,
            title="Subscription Course",
            description="Paid course",
            access_type=Course.ACCESS_SUBSCRIPTION,
        )
        self.client.force_authenticate(self.student)

    def test_free_course_enrolls_without_payment_method(self):
        response = self.client.post(reverse("enroll", args=[self.free_course.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Enrolled successfully")

    def test_subscription_course_requires_payment_method(self):
        response = self.client.post(reverse("enroll", args=[self.subscription_course.id]))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["error"],
            "Choose a valid payment method for subscription enrollment.",
        )

    def test_subscription_course_enrolls_with_payment_method(self):
        response = self.client.post(
            reverse("enroll", args=[self.subscription_course.id]),
            {
                "payment_method": "qr",
                "payment_reference": "UPI123456",
                "payment_confirmed": True,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Enrolled successfully")

    def test_subscription_course_requires_payment_confirmation(self):
        response = self.client.post(
            reverse("enroll", args=[self.subscription_course.id]),
            {
                "payment_method": "qr",
                "payment_reference": "UPI123456",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["error"],
            "Please confirm that payment is completed.",
        )

    def test_subscription_course_requires_payment_reference(self):
        response = self.client.post(
            reverse("enroll", args=[self.subscription_course.id]),
            {
                "payment_method": "card",
                "payment_reference": "123",
                "payment_confirmed": True,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["error"],
            "Enter a valid payment reference (minimum 6 characters).",
        )

    def test_enrollment_list_hides_unverified_subscription_enrollments(self):
        Enrollment.objects.create(
            student=self.student,
            course=self.subscription_course,
            payment_verified=False,
            payment_method="qr",
            payment_reference="UPI123456",
        )
        response = self.client.get(reverse("enrollment-detail"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)
