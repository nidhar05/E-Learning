from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class Notification(models.Model):
    TYPE_COMMENT = "comment"
    TYPE_COMMENT_REPLY = "comment_reply"
    TYPE_ENROLLMENT = "enrollment"
    TYPE_NEW_LESSON = "new_lesson"

    TYPE_CHOICES = [
        (TYPE_COMMENT, "Comment"),
        (TYPE_COMMENT_REPLY, "Comment Reply"),
        (TYPE_ENROLLMENT, "Enrollment"),
        (TYPE_NEW_LESSON, "New Lesson"),
    ]

    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    notification_type = models.CharField(
        max_length=40,
        choices=TYPE_CHOICES,
        default=TYPE_COMMENT,
    )

    message = models.TextField()

    course = models.ForeignKey(
        "courses.Course",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="notifications",
    )

    video = models.ForeignKey(
        "videos.Video",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="notifications",
    )

    comment = models.ForeignKey(
        "comments.Comment",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="notifications",
    )

    is_read = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.sender} → {self.receiver}"
