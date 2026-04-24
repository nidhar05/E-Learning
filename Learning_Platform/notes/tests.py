from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from courses.models import Course
from videos.content_processor import ContentExtractor
from videos.models import Video

from .models import VideoNotes
from .views import auto_create_notes

User = get_user_model()


class VideoNotesGenerationTest(TestCase):
    def setUp(self):
        self.instructor = User.objects.create_user(
            username="instructor1",
            password="testpass123",
            role="instructor",
        )
        User.objects.create_user(
            username="student1",
            password="testpass123",
            role="student",
        )
        self.course = Course.objects.create(
            instructor=self.instructor,
            title="Python Basics",
            description="Introductory Python course",
        )
        self.video = Video.objects.create(
            course=self.course,
            title="Variables",
            original_file=SimpleUploadedFile(
                "variables.mp4",
                b"video-content",
                content_type="video/mp4",
            ),
            duration=12,
            order=1,
            subtitle_text=(
                "A variable is a named container used to store a value in Python. "
                "The assignment operator is the equals sign and it connects a name to data. "
                "The print function is used to display the value stored in a variable. "
                "A string means text data written inside quotes. "
                "A number refers to numeric data that can be used in calculations."
            ),
        )

    def test_create_structured_notes_uses_meaningful_sections_and_terms(self):
        notes = ContentExtractor.create_structured_notes(self.video, self.video.subtitle_text)

        self.assertEqual(notes.sections.count(), 0)
        self.assertIn("## Lesson Summary", notes.content)
        self.assertIn("## Learning Objectives", notes.content)
        self.assertIn("## Core Concepts Explained", notes.content)
        self.assertIn("## Important Terms", notes.content)
        self.assertIn("## Interview Preparation Points", notes.content)
        self.assertIn("A named container used to store a value in Python", notes.important_terms)
        self.assertIn(
            "- A variable is a named container used to store a value in Python.",
            notes.key_takeaways,
        )
        self.assertNotIn("you are", notes.content.lower())
        self.assertNotIn("i am", notes.content.lower())

    def test_auto_create_notes_replaces_placeholder_content(self):
        VideoNotes.objects.create(
            video=self.video,
            title="Notes: Variables",
            content="Notes for video: Variables\n\nAdd comprehensive notes here.",
            key_takeaways="Key takeaways:\n- Point 1",
            important_terms="Glossary:\nTerm 1: Definition",
            is_ai_generated=True,
            is_published=True,
        )

        notes = auto_create_notes(self.video)

        self.assertTrue(notes.is_ai_generated)
        self.assertNotIn("Add comprehensive notes here.", notes.content)
        self.assertEqual(notes.sections.count(), 0)
