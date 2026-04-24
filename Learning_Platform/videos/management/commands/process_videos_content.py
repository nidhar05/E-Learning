from django.core.management.base import BaseCommand

from videos.content_processor import VideoContentProcessor
from videos.models import Video


class Command(BaseCommand):
    help = "Process videos: extract content, generate notes, MCQ questions, and subtitles"

    def add_arguments(self, parser):
        parser.add_argument(
            "video_ids",
            nargs="?",
            type=int,
            help="Specific video ID to process (optional). If not provided, processes all videos.",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Process all videos",
        )
        parser.add_argument(
            "--subtitle-text",
            type=str,
            help="Direct subtitle/content text to use",
        )
        parser.add_argument(
            "--force-transcription",
            action="store_true",
            help="Regenerate subtitles from the video's audio even when subtitle text/file already exists.",
        )

    def handle(self, *args, **options):
        video_id = options.get("video_ids")
        process_all = options.get("all", False)
        subtitle_text = options.get("subtitle_text")
        force_transcription = options.get("force_transcription", False)

        if video_id:
            videos = Video.objects.filter(id=video_id)
            if not videos.exists():
                self.stdout.write(self.style.ERROR(f"Video {video_id} not found"))
                return
        elif process_all or not video_id:
            videos = Video.objects.all()
        else:
            self.stdout.write(self.style.ERROR("Specify video ID or use --all"))
            return

        self.stdout.write(f"Processing {videos.count()} videos...")

        total_notes = 0
        total_questions = 0
        total_subtitles = 0

        for video in videos:
            try:
                result = VideoContentProcessor.process_video(
                    video,
                    subtitle_text,
                    force_transcription=force_transcription,
                )

                total_notes += 1
                total_questions += result["quiz_questions"]
                if result.get("subtitle_generated"):
                    total_subtitles += 1

                subtitle_status = (
                    "[OK] Subtitles" if result.get("subtitle_generated") else "[X] No subtitles"
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"[OK] Video '{video.title}' - "
                        f"Quiz: {result['quiz_questions']} MCQ, "
                        f"Notes: {result['notes_sections']} sections, "
                        f"{subtitle_status}"
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"[X] Error processing video '{video.title}': {str(e)}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n[OK] Completed:\n"
                f"  - Videos processed: {total_notes}\n"
                f"  - MCQ questions created: {total_questions}\n"
                f"  - Subtitle files generated: {total_subtitles}/{total_notes}\n"
                f"  - Average questions per video: {total_questions // max(total_notes, 1)}"
            )
        )
