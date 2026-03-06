from django.db import models
from django.conf import settings

class Course(models.Model):
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    thumbnail = models.ImageField(upload_to='thumbnails/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    