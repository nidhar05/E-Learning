from django.db import models
from django.conf import settings
from videos.models import Video

User = settings.AUTH_USER_MODEL


class Progress(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    video = models.ForeignKey(
        Video,
        on_delete=models.CASCADE
    )

    watch_time = models.IntegerField(
        default=0
    )

    completed = models.BooleanField(
        default=False
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        unique_together = ("user", "video")

    def __str__(self):
        return f"{self.user} - {self.video}"