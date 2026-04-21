from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from videos.models import Video
from quiz.models import Quiz, QuizQuestion
import json

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate quiz template for a video'

    def add_arguments(self, parser):
        parser.add_argument('video_id', type=int, help='Video ID')
        parser.add_argument('--title', type=str, help='Quiz title')
        parser.add_argument('--num-questions', type=int, default=5, help='Number of questions')

    def handle(self, *args, **options):
        video_id = options['video_id']
        title = options.get('title')
        num_questions = options.get('num_questions', 5)

        try:
            video = Video.objects.get(pk=video_id)
        except Video.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Video with ID {video_id} not found'))
            return

        # Check if quiz already exists
        if hasattr(video, 'quiz'):
            self.stdout.write(self.style.WARNING(f'Quiz already exists for video: {video.title}'))
            return

        quiz_title = title or f"{video.title} - Quiz"
        
        # Create quiz
        quiz = Quiz.objects.create(
            video=video,
            title=quiz_title,
            description=f"Quiz for {video.title}",
            passing_score=70,
            max_attempts=3
        )

        # Create sample questions
        sample_questions = [
            {
                'question_type': 'multiple_choice',
                'question_text': f'What was the main topic of the {video.title} video?',
                'option_a': 'Option A',
                'option_b': 'Option B',
                'option_c': 'Option C',
                'option_d': 'Option D',
                'correct_answer': 'A',
                'explanation': 'This is the correct answer.'
            },
            {
                'question_type': 'true_false',
                'question_text': f'The content in {video.title} covers advanced topics.',
                'correct_answer': 'True',
                'explanation': 'This statement is correct.'
            },
            {
                'question_type': 'short_answer',
                'question_text': f'Briefly summarize the key points from {video.title}.',
                'correct_answer': 'Key points summary',
                'explanation': 'Any comprehensive summary is acceptable.'
            }
        ]

        for idx, q in enumerate(sample_questions[:num_questions], 1):
            QuizQuestion.objects.create(
                quiz=quiz,
                question_type=q['question_type'],
                question_text=q['question_text'],
                option_a=q.get('option_a', ''),
                option_b=q.get('option_b', ''),
                option_c=q.get('option_c', ''),
                option_d=q.get('option_d', ''),
                correct_answer=q['correct_answer'],
                explanation=q.get('explanation', ''),
                order=idx,
                points=1
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created quiz "{quiz_title}" with {num_questions} questions'
            )
        )
