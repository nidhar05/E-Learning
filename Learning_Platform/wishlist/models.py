from django.db import models
from django.conf import settings
from courses.models import Course


class Wishlist(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE
    )

    added_at = models.DateTimeField(
        auto_now_add=True
    )