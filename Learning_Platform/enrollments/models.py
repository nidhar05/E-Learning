from django.db import models
from django.conf import settings
from courses.models import Course

class Enrollment(models.Model):
    PAYMENT_QR = "qr"
    PAYMENT_CARD = "card"
    PAYMENT_METHOD_CHOICES = [
        (PAYMENT_QR, "QR"),
        (PAYMENT_CARD, "Card"),
    ]

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, null=True, blank=True)
    payment_reference = models.CharField(max_length=120, null=True, blank=True)
    payment_verified = models.BooleanField(default=False)

    class Meta:
        unique_together = ('student', 'course')
        
