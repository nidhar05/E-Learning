from django.db import models
from courses.models import Course

class Video(models.Model):

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='videos'
    )

    title = models.CharField(max_length=255)

    original_file = models.FileField(upload_to="uploads/")

    processed_file = models.FileField(upload_to="videos/", null=True, blank=True)
    
    # Subtitles support
    subtitle_file = models.FileField(upload_to="subtitles/", null=True, blank=True, help_text="VTT or SRT subtitle file")
    
    subtitle_text = models.TextField(blank=True, null=True, help_text="Extracted text from subtitles or video content")

    duration = models.IntegerField()

    order = models.IntegerField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.title