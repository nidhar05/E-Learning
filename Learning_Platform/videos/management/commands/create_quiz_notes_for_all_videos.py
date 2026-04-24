from django.core.management.base import BaseCommand
from django.db import transaction
from videos.models import Video
from quiz.models import Quiz, QuizQuestion
from notes.models import VideoNotes, NoteSection


class Command(BaseCommand):
    help = 'Auto-create Quiz and Notes for all videos that don\'t have them'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Recreate quiz and notes even if they already exist',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        force = options.get('force', False)
        
        all_videos = Video.objects.all()
        self.stdout.write(f"Processing {all_videos.count()} videos...")
        
        created_quizzes = 0
        created_notes = 0
        skipped = 0
        
        for video in all_videos:
            try:
                # Create Quiz if it doesn't exist
                if force or not hasattr(video, 'quiz'):
                    quiz, quiz_created = Quiz.objects.get_or_create(
                        video=video,
                        defaults={
                            'title': f"Quiz: {video.title}",
                            'description': f"Auto-generated quiz for video: {video.title}",
                            'passing_score': 70,
                            'time_limit': 30,
                            'max_attempts': 0,
                            'is_published': True
                        }
                    )
                    
                    if quiz_created:
                        created_quizzes += 1
                        # Add sample question
                        if not quiz.questions.exists():
                            QuizQuestion.objects.create(
                                quiz=quiz,
                                question_text=f"Summarize the key points from '{video.title}'",
                                question_type='essay',
                                points=10,
                                order=1
                            )
                
                # Create Notes if they don't exist
                if force or not hasattr(video, 'notes'):
                    notes, notes_created = VideoNotes.objects.get_or_create(
                        video=video,
                        defaults={
                            'title': f"Notes: {video.title}",
                            'content': f"Notes for video: {video.title}\n\nAdd comprehensive notes here.",
                            'key_takeaways': "Key takeaways:\n• Point 1\n• Point 2\n• Point 3",
                            'important_terms': "Glossary:\nTerm 1: Definition\nTerm 2: Definition",
                            'is_ai_generated': True,
                            'is_published': True
                        }
                    )
                    
                    if notes_created:
                        created_notes += 1
                        # Add sample section
                        if not notes.sections.exists():
                            NoteSection.objects.create(
                                notes=notes,
                                title="Introduction",
                                content="Overview of the main concepts",
                                order=1
                            )
                else:
                    skipped += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Error processing video '{video.title}' (ID: {video.id}): {str(e)}"
                    )
                )
                continue
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\n✓ Completed:\n"
                f"  - Quizzes created: {created_quizzes}\n"
                f"  - Notes created: {created_notes}\n"
                f"  - Videos skipped: {skipped}\n"
                f"  - Total quizzes: {Quiz.objects.count()}\n"
                f"  - Total notes: {VideoNotes.objects.count()}"
            )
        )
