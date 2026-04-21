from django.core.management.base import BaseCommand
from videos.models import Video
from notes.models import VideoNotes, NoteSection

User = None


class Command(BaseCommand):
    help = 'Generate notes template for a video'

    def add_arguments(self, parser):
        parser.add_argument('video_id', type=int, help='Video ID')
        parser.add_argument('--title', type=str, help='Notes title')
        parser.add_argument('--num-sections', type=int, default=3, help='Number of sections')

    def handle(self, *args, **options):
        video_id = options['video_id']
        title = options.get('title')
        num_sections = options.get('num_sections', 3)

        try:
            video = Video.objects.get(pk=video_id)
        except Video.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Video with ID {video_id} not found'))
            return

        # Check if notes already exist
        if hasattr(video, 'notes'):
            self.stdout.write(self.style.WARNING(f'Notes already exist for video: {video.title}'))
            return

        notes_title = title or f"{video.title} - Notes"
        
        # Create notes
        notes = VideoNotes.objects.create(
            video=video,
            title=notes_title,
            content=f"# {notes_title}\n\nMain notes content for {video.title}",
            key_takeaways="- Key point 1\n- Key point 2\n- Key point 3",
            important_terms="- Term 1: Definition\n- Term 2: Definition\n- Term 3: Definition",
            is_ai_generated=True
        )

        # Create sample sections
        sample_sections = [
            {
                'title': 'Introduction',
                'content': '# Introduction\n\nThis section covers the introduction to ' + video.title,
                'icon': '📌'
            },
            {
                'title': 'Main Concepts',
                'content': '# Main Concepts\n\nKey concepts covered in ' + video.title,
                'icon': '💡'
            },
            {
                'title': 'Conclusion',
                'content': '# Conclusion\n\nSummary and conclusion of ' + video.title,
                'icon': '✅'
            },
            {
                'title': 'Further Reading',
                'content': '# Further Reading\n\nAdditional resources for ' + video.title,
                'icon': '📚'
            },
            {
                'title': 'Practice Exercises',
                'content': '# Practice Exercises\n\nExercises to practice what you learned.',
                'icon': '✋'
            }
        ]

        for idx, section_data in enumerate(sample_sections[:num_sections], 1):
            NoteSection.objects.create(
                notes=notes,
                title=section_data['title'],
                content=section_data['content'],
                icon=section_data.get('icon', ''),
                order=idx
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created notes "{notes_title}" with {num_sections} sections'
            )
        )
