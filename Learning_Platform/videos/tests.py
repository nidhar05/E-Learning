from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, RequestFactory, SimpleTestCase, TestCase, override_settings

from courses.models import Course
from .content_processor import VideoContentProcessor
from .models import Video
from .serializers import VideoSerializer
from .subtitle_utils import build_srt_from_segments, build_vtt_from_plain_text, subtitle_file_has_synthetic_timing

User = get_user_model()


class SubtitleFallbackGenerationTest(SimpleTestCase):
    def test_build_vtt_from_plain_text_creates_webvtt_cues(self):
        text = (
            "Python variables store values. "
            "A variable name should be clear and descriptive."
        )

        vtt_content = build_vtt_from_plain_text(text)

        self.assertIn("WEBVTT", vtt_content)
        self.assertIn("-->", vtt_content)
        self.assertIn("X-TIMING-SOURCE: plain-text-estimate", vtt_content)
        self.assertIn("Python variables store values", vtt_content)

    def test_plain_text_vtt_is_marked_as_synthetic_timing(self):
        vtt_content = build_vtt_from_plain_text(
            "Python variables store values. Clear names improve readability."
        )

        self.assertTrue(
            subtitle_file_has_synthetic_timing(ContentFile(vtt_content.encode("utf-8")))
        )

    def test_word_timestamps_create_short_synchronized_cues(self):
        segments = [
            type(
                "Segment",
                (),
                {
                    "start": 0.0,
                    "end": 8.0,
                    "text": "Python variables store values and clear names improve readability",
                    "words": [
                        type("Word", (), {"start": 0.1, "end": 0.4, "word": "Python"}),
                        type("Word", (), {"start": 0.45, "end": 0.8, "word": "variables"}),
                        type("Word", (), {"start": 0.85, "end": 1.1, "word": "store"}),
                        type("Word", (), {"start": 1.15, "end": 1.5, "word": "values"}),
                        type("Word", (), {"start": 4.1, "end": 4.35, "word": "clear"}),
                        type("Word", (), {"start": 4.4, "end": 4.7, "word": "names"}),
                        type("Word", (), {"start": 4.75, "end": 5.2, "word": "improve"}),
                        type("Word", (), {"start": 5.25, "end": 5.8, "word": "readability"}),
                    ],
                },
            )()
        ]

        srt_content = build_srt_from_segments(segments)

        self.assertIn("00:00:00,100 --> 00:00:01,500", srt_content)
        self.assertIn("00:00:04,100 --> 00:00:05,800", srt_content)


class VideoProcessingHonestyTest(TestCase):
    def setUp(self):
        self.instructor = User.objects.create_user(
            username="subtitle_instructor",
            password="testpass123",
            role="instructor",
        )
        self.course = Course.objects.create(
            instructor=self.instructor,
            title="Subtitle Honesty Course",
            description="Test course",
        )
        self.video = Video.objects.create(
            course=self.course,
            title="Long Video",
            original_file=SimpleUploadedFile(
                "long_video.mp4",
                b"video-content",
                content_type="video/mp4",
            ),
            duration=600,
            order=1,
        )

    @patch("videos.content_processor.AudioTranscriber.is_available", return_value=False)
    def test_process_video_does_not_generate_fake_subtitles_without_transcript(self, _mock_available):
        result = VideoContentProcessor.process_video(self.video)
        self.video.refresh_from_db()

        self.assertEqual(result["subtitle_generated"], False)
        self.assertEqual(result["subtitle_text_length"], 0)
        self.assertFalse(self.video.subtitle_text)
        self.assertFalse(self.video.subtitle_file)

    @patch("videos.content_processor.AudioTranscriber.is_available", return_value=False)
    def test_needs_processing_when_subtitle_file_reference_is_missing(self, _mock_available):
        self.video.subtitle_text = (
            "Variables store values in Python and help us reuse data in a readable way."
        )
        self.video.subtitle_file.name = "subtitles/missing_long_video.vtt"
        self.video.save(update_fields=["subtitle_text", "subtitle_file"])

        self.assertTrue(VideoContentProcessor.needs_processing(self.video))

    @patch("videos.content_processor.AudioTranscriber.is_available", return_value=True)
    def test_needs_processing_when_subtitle_timing_is_synthetic(self, _mock_available):
        self.video.subtitle_text = (
            "Variables store values in Python. "
            "Clear variable names improve readability and maintenance."
        )
        self.video.subtitle_file.save(
            "subtitles/synthetic_timing.vtt",
            ContentFile(build_vtt_from_plain_text(self.video.subtitle_text).encode("utf-8")),
            save=True,
        )

        self.assertTrue(VideoContentProcessor.needs_processing(self.video))

    @patch("videos.content_processor.AudioTranscriber.is_available", return_value=False)
    def test_process_video_does_not_make_subtitles_from_untimed_transcript_text(self, _mock_available):
        self.video.subtitle_text = (
            "Variables store values in Python. "
            "Clear variable names improve readability and maintenance."
        )
        self.video.save(update_fields=["subtitle_text"])

        result = VideoContentProcessor.process_video(self.video)
        self.video.refresh_from_db()

        self.assertFalse(result["subtitle_generated"])
        self.assertFalse(self.video.subtitle_file)

    @override_settings(ALLOWED_HOSTS=["localhost", "testserver"])
    @patch("videos.content_processor.AudioTranscriber.is_available", return_value=False)
    def test_serializer_and_stream_use_direct_stream_urls_without_redirect(self, _mock_available):
        self.video.subtitle_text = (
            "Variables store values in Python. "
            "Clear variable names improve readability and maintenance."
        )
        self.video.subtitle_file.save(
            "subtitles/timed_subtitle.vtt",
            ContentFile(b"WEBVTT\n\n1\n00:00:00.000 --> 00:00:02.000\nVariables store values\n"),
            save=True,
        )
        self.video.refresh_from_db()

        request = RequestFactory().get("/api/videos/1/", HTTP_HOST="localhost:8000")
        data = VideoSerializer(self.video, context={"request": request}).data

        self.assertTrue(data["subtitle_url"].endswith("/"))
        self.assertTrue(data["video_url"].endswith("/"))

        client = Client(HTTP_HOST="localhost:8000")
        subtitle_response = client.get(f"/api/videos/stream/{self.video.subtitle_file.name}")

        self.assertEqual(subtitle_response.status_code, 200)

    @override_settings(ALLOWED_HOSTS=["localhost", "testserver"])
    @patch("videos.content_processor.AudioTranscriber.is_available", return_value=False)
    def test_stream_route_handles_trailing_slash_in_captured_path(self, _mock_available):
        self.video.subtitle_file.save(
            "subtitles/test_video_20_subtitles.vtt",
            ContentFile(b"WEBVTT\n\n1\n00:00:00.000 --> 00:00:02.000\nHello world\n"),
            save=True,
        )

        client = Client(HTTP_HOST="localhost:8000")
        subtitle_response = client.get(f"/api/videos/stream/{self.video.subtitle_file.name}/")

        self.assertEqual(subtitle_response.status_code, 200)
