from django.db import models
from django.conf import settings

class Course(models.Model):
    ACCESS_FREE = "free"
    ACCESS_SUBSCRIPTION = "subscription"
    ACCESS_TYPE_CHOICES = [
        (ACCESS_FREE, "Free"),
        (ACCESS_SUBSCRIPTION, "Subscription"),
    ]

    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    access_type = models.CharField(
        max_length=20,
        choices=ACCESS_TYPE_CHOICES,
        default=ACCESS_FREE,
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    thumbnail = models.ImageField(upload_to='thumbnails/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
