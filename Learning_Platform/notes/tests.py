from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class VideoNotesTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            role='student'
        )


class VideoNotesModelTest(VideoNotesTestCase):
    pass
