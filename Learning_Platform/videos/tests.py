from django.test import SimpleTestCase

from .subtitle_utils import build_vtt_from_plain_text


class SubtitleFallbackGenerationTest(SimpleTestCase):
    def test_build_vtt_from_plain_text_creates_webvtt_cues(self):
        text = (
            "Python variables store values. "
            "A variable name should be clear and descriptive."
        )

        vtt_content = build_vtt_from_plain_text(text)

        self.assertIn("WEBVTT", vtt_content)
        self.assertIn("-->", vtt_content)
        self.assertIn("Python variables store values", vtt_content)

