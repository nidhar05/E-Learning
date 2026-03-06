from django.db import models
from courses.models import Course

class Video(models.Model):

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='videos'
    )

    title = models.CharField(max_length=255)

    video_file = models.FileField(
        upload_to='videos/'
    )

    duration = models.IntegerField()

    order = models.IntegerField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.title