from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from courses.models import Course
from videos.content_processor import MCQGenerator
from videos.models import Video

from .models import UserQuizAttempt
from .views import auto_create_quiz

User = get_user_model()


class QuizGenerationTest(TestCase):
    def setUp(self):
        self.instructor = User.objects.create_user(
            username="instructor1",
            password="testpass123",
            role="instructor",
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

    def test_mcq_generator_creates_multiple_choice_questions_from_video_text(self):
        questions = MCQGenerator.generate_mcq_from_text(self.video.subtitle_text, num_questions=5)

        self.assertGreaterEqual(len(questions), 3)
        self.assertTrue(all(question["type"] == "multiple_choice" for question in questions))
        self.assertTrue(all(len(question["options"]) == 4 for question in questions))
        self.assertTrue(
            any(
                any(prefix in question["question"] for prefix in ["What is", "What does", "Which statement"])
                for question in questions
            )
        )

    def test_auto_create_quiz_builds_mcq_quiz_from_video_content(self):
        quiz = auto_create_quiz(self.video)
        expected_count = MCQGenerator.determine_question_count(self.video.subtitle_text)

        self.assertEqual(quiz.questions.count(), expected_count)
        self.assertTrue(all(question.question_type == "multiple_choice" for question in quiz.questions.all()))
        self.assertFalse(quiz.questions.filter(question_type="essay").exists())
        self.assertEqual(quiz.max_attempts, 0)

    def test_determine_question_count_stays_proportional_to_content_length(self):
        short_text = (
            "A variable stores a value in Python. "
            "The print function displays output."
        )
        long_text = " ".join([self.video.subtitle_text] * 8)

        self.assertEqual(MCQGenerator.determine_question_count(short_text), 3)
        self.assertGreater(MCQGenerator.determine_question_count(long_text), 3)
        self.assertLessEqual(MCQGenerator.determine_question_count(long_text), 10)

    def test_generate_mcq_from_text_respects_requested_question_count(self):
        questions = MCQGenerator.generate_mcq_from_text(
            self.video.subtitle_text,
            num_questions=4,
            lesson_title=self.video.title,
        )

        self.assertGreaterEqual(len(questions), 3)
        self.assertLessEqual(len(questions), 4)

    def test_auto_create_quiz_does_not_create_fake_subtitles_for_untranscribed_video(self):
        video = Video.objects.create(
            course=self.course,
            title="Introduction",
            original_file=SimpleUploadedFile(
                "introduction.mp4",
                b"video-content",
                content_type="video/mp4",
            ),
            duration=150,
            order=2,
        )

        quiz = auto_create_quiz(video)
        video.refresh_from_db()

        self.assertFalse(video.subtitle_text)
        self.assertFalse(video.subtitle_file)
        self.assertEqual(quiz.questions.count(), 0)


class QuizAttemptFlowTest(TestCase):
    def setUp(self):
        self.instructor = User.objects.create_user(
            username="attempt_instructor",
            password="testpass123",
            role="instructor",
        )
        self.student = User.objects.create_user(
            username="attempt_student",
            password="testpass123",
            role="student",
        )
        self.course = Course.objects.create(
            instructor=self.instructor,
            title="Quiz Flow Course",
            description="Test course",
        )
        self.video = Video.objects.create(
            course=self.course,
            title="Quiz Flow Video",
            original_file=SimpleUploadedFile(
                "quiz_flow.mp4",
                b"video-content",
                content_type="video/mp4",
            ),
            duration=10,
            order=1,
            subtitle_text=(
                "A variable is a named container used to store a value. "
                "The print function is used to display output."
            ),
        )
        self.quiz = auto_create_quiz(self.video)
        self.client = APIClient()
        self.client.force_authenticate(user=self.student)

    def test_start_quiz_reuses_existing_in_progress_attempt(self):
        existing = UserQuizAttempt.objects.create(
            user=self.student,
            quiz=self.quiz,
            attempt_number=1,
            status="in_progress",
        )

        response = self.client.post(
            "/api/quiz/attempts/start_quiz/",
            {"quiz_id": self.quiz.id},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], existing.id)
        self.assertEqual(
            UserQuizAttempt.objects.filter(user=self.student, quiz=self.quiz).count(),
            1,
        )

    def test_start_quiz_uses_next_attempt_number_after_existing_attempts(self):
        UserQuizAttempt.objects.create(
            user=self.student,
            quiz=self.quiz,
            attempt_number=1,
            status="graded",
            score=80,
            total_points=10,
            earned_points=8,
        )

        response = self.client.post(
            "/api/quiz/attempts/start_quiz/",
            {"quiz_id": self.quiz.id},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["attempt_number"], 2)
