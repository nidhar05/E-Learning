from unittest.mock import patch

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
            amount=499,
        )
        self.client.force_authenticate(self.student)

    @staticmethod
    def _mock_gateway(order_id="order_test_123"):
        class MockUtility:
            @staticmethod
            def verify_payment_signature(_payload):
                return None

        class MockOrder:
            @staticmethod
            def create(data):
                return {
                    "id": order_id,
                    "amount": data["amount"],
                    "currency": data.get("currency", "INR"),
                }

        class MockClient:
            order = MockOrder()
            utility = MockUtility()

        return MockClient()

    def test_free_course_enrolls_without_payment_method(self):
        response = self.client.post(reverse("enroll", args=[self.free_course.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Enrolled successfully")

    def test_subscription_course_requires_verified_payment(self):
        response = self.client.post(reverse("enroll", args=[self.subscription_course.id]))

        self.assertEqual(response.status_code, 402)
        self.assertEqual(
            response.data["error"],
            "Subscription course requires payment. Use QR (with UTR) or card gateway.",
        )

    def test_subscription_course_enrolls_with_qr_and_utr(self):
        response = self.client.post(
            reverse("enroll", args=[self.subscription_course.id]),
            {
                "payment_method": "qr",
                "payment_reference": "UTR123456",
                "payment_confirmed": True,
            },
        )

        self.assertEqual(response.status_code, 200)
        enrollment = Enrollment.objects.get(student=self.student, course=self.subscription_course)
        self.assertTrue(enrollment.payment_verified)
        self.assertEqual(enrollment.payment_reference, "UTR123456")

    @patch("enrollments.views._get_razorpay_client")
    def test_subscription_payment_order_creation(self, mock_get_client):
        mock_get_client.return_value = (self._mock_gateway(), "rzp_test_key", None)
        response = self.client.post(
            reverse("subscription-payment-create-order", args=[self.subscription_course.id]),
            {"payment_method": "qr"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["order_id"], "order_test_123")
        self.assertEqual(response.data["razorpay_key_id"], "rzp_test_key")
        self.assertFalse(
            Enrollment.objects.get(student=self.student, course=self.subscription_course).payment_verified
        )

    @patch("enrollments.views._get_razorpay_client")
    def test_subscription_payment_verification_enrolls_student(self, mock_get_client):
        mock_get_client.return_value = (self._mock_gateway(order_id="order_test_789"), "rzp_test_key", None)
        self.client.post(
            reverse("subscription-payment-create-order", args=[self.subscription_course.id]),
            {"payment_method": "card"},
        )
        response = self.client.post(
            reverse("subscription-payment-verify", args=[self.subscription_course.id]),
            {
                "payment_method": "card",
                "razorpay_order_id": "order_test_789",
                "razorpay_payment_id": "pay_test_789",
                "razorpay_signature": "sig_test_789",
            },
        )

        self.assertEqual(response.status_code, 200)
        enrollment = Enrollment.objects.get(student=self.student, course=self.subscription_course)
        self.assertTrue(enrollment.payment_verified)
        self.assertEqual(enrollment.payment_reference, "pay_test_789")

    def test_enrollment_list_hides_unverified_subscription_enrollments(self):
        Enrollment.objects.create(
            student=self.student,
            course=self.subscription_course,
            payment_verified=False,
            payment_method="qr",
            payment_reference="order_test_pending",
        )
        response = self.client.get(reverse("enrollment-detail"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)
