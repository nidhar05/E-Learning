"""
Service for extracting content from videos and generating structured notes,
subtitle files, and MCQ questions.
"""

import random

from notes.models import NoteSection, VideoNotes
from quiz.models import Quiz, QuizQuestion

from .subtitle_utils import (
    AudioTranscriber,
    SubtitleParser,
    convert_srt_to_vtt,
    save_vtt_file,
    safe_log,
)


class ContentExtractor:
    """Extracts content from subtitles or plain text and generates notes."""

    @staticmethod
    def extract_key_points(text, max_points=5):
        if not text:
            return []

        sentences = text.split(".")
        sentences = [sentence.strip() for sentence in sentences if len(sentence.strip()) > 20]
        return sentences[:max_points]

    @staticmethod
    def extract_terms(text):
        if not text:
            return {}

        terms = {}
        keywords = ["is", "means", "defined as", "refers to"]

        for sentence in text.split("."):
            lower_sentence = sentence.lower()
            for keyword in keywords:
                if keyword not in lower_sentence:
                    continue

                parts = sentence.split(keyword)
                if len(parts) < 2:
                    continue

                term = parts[0].strip().split()[-1] if parts[0].strip() else ""
                definition = parts[1].strip()[:150] if parts[1].strip() else ""
                if term and definition:
                    terms[term] = definition

        return terms

    @staticmethod
    def create_structured_notes(video, content_text):
        notes, created = VideoNotes.objects.get_or_create(
            video=video,
            defaults={
                "title": f"Notes: {video.title}",
                "content": content_text or f"Notes for video: {video.title}",
                "is_ai_generated": True,
                "is_published": True,
            },
        )

        if not created:
            notes.content = content_text or notes.content
            notes.save()

        if content_text:
            if not created:
                notes.sections.all().delete()

            key_points = ContentExtractor.extract_key_points(content_text)
            for idx, point in enumerate(key_points):
                NoteSection.objects.create(
                    notes=notes,
                    title=f"Point {idx + 1}",
                    content=point,
                    order=idx,
                )

            terms = ContentExtractor.extract_terms(content_text)
            if terms:
                glossary_text = "\n".join(
                    [f"- {term}: {definition}" for term, definition in list(terms.items())[:10]]
                )
                NoteSection.objects.create(
                    notes=notes,
                    title="Key Glossary",
                    content=glossary_text,
                    order=len(key_points),
                )

            notes.key_takeaways = "\n".join([f"- {point}" for point in key_points])
            notes.important_terms = "\n".join(
                [f"{term}: {definition}" for term, definition in list(terms.items())[:5]]
            )
            notes.save()

        return notes


class MCQGenerator:
    """Generates multiple-choice questions from text content."""

    @staticmethod
    def generate_mcq_from_text(text, num_questions=3):
        if not text or len(text.strip()) < 50:
            return []

        questions = []
        sentences = [sentence.strip() for sentence in text.split(".") if len(sentence.strip()) > 20]

        for sentence in sentences[:num_questions]:
            words = sentence.split()
            if len(words) < 5:
                continue

            subject = " ".join(words[:3]) if len(words) >= 3 else sentence
            question = {
                "type": "multiple_choice",
                "question": f"According to the content, {subject.lower()}?",
                "options": [
                    f"{sentence.strip()[:100]}...",
                    "It refers to a different concept mentioned.",
                    "This is not explicitly stated in the content.",
                    "It is the opposite of what was described.",
                ],
                "correct_answer": "A",
                "explanation": f"Based on the content: {sentence.strip()[:150]}",
            }

            correct_option = question["options"][0]
            wrong_options = question["options"][1:]
            random.shuffle(wrong_options)
            question["options"] = [correct_option] + wrong_options
            questions.append(question)

        return questions

    @staticmethod
    def create_mcq_quiz(video, quiz_obj, questions_data):
        if not questions_data:
            return

        quiz_obj.questions.all().delete()

        for idx, q_data in enumerate(questions_data):
            options = list(q_data.get("options", []))
            correct_answer = q_data.get("correct_answer", "A")

            while len(options) < 4:
                options.append("Not available")

            QuizQuestion.objects.create(
                quiz=quiz_obj,
                question_type="multiple_choice",
                question_text=q_data.get("question", "Quiz question"),
                option_a=options[0],
                option_b=options[1],
                option_c=options[2],
                option_d=options[3],
                correct_answer=correct_answer,
                explanation=q_data.get("explanation", ""),
                points=5,
                order=idx,
            )


class VideoContentProcessor:
    """Main processor for video content extraction and subtitle generation."""

    @staticmethod
    def _build_fallback_text(video):
        return (
            f"This video covers: {video.title}. "
            f"Key topics include an introduction to {video.title}, main concepts and principles, "
            "practical applications, and a summary with core takeaways."
        )

    @staticmethod
    def _looks_like_fallback_text(text):
        normalized = (text or "").strip().lower()
        return normalized.startswith("this video covers:")

    @staticmethod
    def process_video(video, subtitle_text=None):
        content_text = subtitle_text or (video.subtitle_text or "").strip()
        subtitle_generated = False
        transcript_source = "existing_text" if content_text else "none"
        srt_output = None
        subtitle_file_path = None
        should_attempt_transcription = (
            subtitle_text is None
            and AudioTranscriber.is_available()
            and (
                not video.subtitle_file
                or not content_text
                or VideoContentProcessor._looks_like_fallback_text(content_text)
            )
        )

        safe_log(f"Processing video {video.id}")

        if should_attempt_transcription:
            safe_log("Attempting audio transcription")
            srt_output = AudioTranscriber.transcribe_video(video)

            if srt_output:
                if hasattr(srt_output, "text"):
                    srt_output = srt_output.text

                content_text = SubtitleParser.parse_srt_file(srt_output)
                backend_name = AudioTranscriber.get_backend() or "audio_transcription"
                transcript_source = backend_name
                safe_log("Audio transcription completed")
            else:
                safe_log("Audio transcription did not produce subtitles")

        if not content_text and video.subtitle_file:
            try:
                with video.subtitle_file.open("rb") as subtitle_file_obj:
                    parsed_text = SubtitleParser.extract_text_from_subtitle_file(subtitle_file_obj)
                if parsed_text:
                    content_text = parsed_text
                    transcript_source = "existing_subtitle_file"
            except Exception as e:
                safe_log(f"Subtitle file read error for video {video.id}: {e}")

        if not content_text:
            content_text = VideoContentProcessor._build_fallback_text(video)
            transcript_source = "generated_summary"

        try:
            if srt_output:
                vtt_content = convert_srt_to_vtt(srt_output)
                subtitle_generated = True
                subtitle_file_path = save_vtt_file(video, vtt_content)
                video.subtitle_file = subtitle_file_path
                safe_log(f"Subtitle file saved for video {video.id}")
            elif transcript_source == "existing_subtitle_file" and video.subtitle_file:
                subtitle_generated = True
                subtitle_file_path = video.subtitle_file.name
                safe_log(f"Keeping existing subtitle file for video {video.id}")
            else:
                if video.subtitle_file:
                    video.subtitle_file.delete(save=False)
                video.subtitle_file = None
                safe_log(
                    f"No timed transcript available for video {video.id}; subtitle track cleared"
                )

            video.subtitle_text = content_text
            video.save(update_fields=["subtitle_file", "subtitle_text"])
        except Exception as e:
            safe_log(f"Subtitle save error for video {video.id}: {e}")
            video.subtitle_text = content_text
            video.save(update_fields=["subtitle_text"])

        notes = ContentExtractor.create_structured_notes(video, content_text)
        questions = MCQGenerator.generate_mcq_from_text(content_text, num_questions=5)

        quiz, _ = Quiz.objects.get_or_create(
            video=video,
            defaults={
                "title": f"Quiz: {video.title}",
                "description": f"Multiple Choice Quiz for {video.title}",
                "passing_score": 70,
                "time_limit": 15,
                "max_attempts": 3,
                "is_published": True,
            },
        )
        MCQGenerator.create_mcq_quiz(video, quiz, questions)

        notes_sections = notes.sections.count() if hasattr(notes, "sections") else 0

        return {
            "video_id": video.id,
            "subtitle_generated": subtitle_generated and bool(subtitle_file_path),
            "subtitle_file": subtitle_file_path,
            "subtitle_text_length": len(content_text),
            "transcript_source": transcript_source,
            "quiz_questions": len(questions),
            "notes_sections": notes_sections,
        }
