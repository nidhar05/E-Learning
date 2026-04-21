from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.exceptions import PermissionDenied, ValidationError

from videos.models import Video
from .models import Quiz, QuizQuestion, UserQuizAttempt, UserQuizAnswer
from .serializers import (
    QuizDetailSerializer, QuizListSerializer, UserQuizAttemptDetailSerializer,
    UserQuizAttemptListSerializer, UserQuizAnswerSerializer
)


def auto_create_quiz(video):
    """Auto-create quiz and questions if they don't exist"""
    quiz, created = Quiz.objects.get_or_create(
        video=video,
        defaults={
            'title': f"Quiz: {video.title}",
            'description': f"Auto-generated quiz for video: {video.title}",
            'passing_score': 70,
            'time_limit': 30,
            'max_attempts': 3,
            'is_published': True
        }
    )
    
    if created and not quiz.questions.exists():
        QuizQuestion.objects.create(
            quiz=quiz,
            question_text=f"Summarize the key points from '{video.title}'",
            question_type='essay',
            points=10,
            order=1
        )
    
    return quiz
from .serializers import (
    QuizDetailSerializer, QuizListSerializer, UserQuizAttemptDetailSerializer,
    UserQuizAttemptListSerializer, UserQuizAnswerSerializer
)


class QuizListView(generics.ListCreateAPIView):
    """List quizzes or create a new quiz (instructor only)"""
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        return Quiz.objects.filter(is_published=True)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return QuizDetailSerializer
        return QuizListSerializer
    
    def perform_create(self, serializer):
        if self.request.user.role != 'instructor':
            raise PermissionDenied("Only instructors can create quizzes")
        
        video = serializer.validated_data.get('video')
        if video.course.instructor != self.request.user:
            raise PermissionDenied("You can only create quizzes for your videos")
        
        serializer.save()


class QuizDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a quiz"""
    queryset = Quiz.objects.all()
    serializer_class = QuizDetailSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def perform_update(self, serializer):
        if self.request.user.role != 'instructor':
            raise PermissionDenied("Only instructors can update quizzes")
        
        if self.get_object().video.course.instructor != self.request.user:
            raise PermissionDenied("You can only update your quizzes")
        
        serializer.save()
    
    def perform_destroy(self, instance):
        if self.request.user.role != 'instructor':
            raise PermissionDenied("Only instructors can delete quizzes")
        
        if instance.video.course.instructor != self.request.user:
            raise PermissionDenied("You can only delete your quizzes")
        
        instance.delete()


class QuizByVideoView(generics.RetrieveAPIView):
    """Get quiz for a specific video - auto-creates if not exists"""
    serializer_class = QuizDetailSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_object(self):
        video_id = self.kwargs.get('video_id')
        video = get_object_or_404(Video, pk=video_id)
        # Auto-create quiz if it doesn't exist
        return auto_create_quiz(video)


class UserQuizAttemptViewSet(viewsets.ModelViewSet):
    """Handle user quiz attempts and answers"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserQuizAttempt.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UserQuizAttemptDetailSerializer
        return UserQuizAttemptListSerializer
    
    @action(detail=False, methods=['post'])
    def start_quiz(self, request):
        """Start a new quiz attempt"""
        quiz_id = request.data.get('quiz_id')
        
        quiz = get_object_or_404(Quiz, pk=quiz_id)
        
        if not quiz.is_published:
            raise PermissionDenied("This quiz is not available")
        
        # Check number of attempts
        current_attempts = UserQuizAttempt.objects.filter(
            user=request.user,
            quiz=quiz
        ).count()
        
        if current_attempts >= quiz.max_attempts:
            raise ValidationError(
                f"You have reached the maximum number of attempts ({quiz.max_attempts})"
            )
        
        # Create new attempt
        attempt = UserQuizAttempt.objects.create(
            user=request.user,
            quiz=quiz,
            attempt_number=current_attempts + 1
        )
        
        return Response(
            UserQuizAttemptDetailSerializer(attempt).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def submit_answer(self, request, pk=None):
        """Submit an answer to a quiz question"""
        attempt = self.get_object()
        
        if attempt.status != 'in_progress':
            raise ValidationError("This quiz attempt is not in progress")
        
        question_id = request.data.get('question_id')
        user_answer = request.data.get('answer')
        
        if not question_id or not user_answer:
            raise ValidationError("Question ID and answer are required")
        
        question = get_object_or_404(
            QuizQuestion,
            pk=question_id,
            quiz=attempt.quiz
        )
        
        # Check if answer already exists
        existing_answer = UserQuizAnswer.objects.filter(
            attempt=attempt,
            question=question
        ).first()
        
        if existing_answer:
            existing_answer.user_answer = user_answer
            existing_answer.save()
        else:
            UserQuizAnswer.objects.create(
                attempt=attempt,
                question=question,
                user_answer=user_answer
            )
        
        return Response(
            {'status': 'Answer recorded', 'question_id': question_id},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def submit_quiz(self, request, pk=None):
        """Submit the quiz for grading"""
        attempt = self.get_object()
        
        if attempt.status != 'in_progress':
            raise ValidationError("This quiz is not in progress")
        
        # Grade the quiz
        self._grade_attempt(attempt)
        
        attempt.status = 'graded'
        attempt.end_time = timezone.now()
        attempt.save()
        
        return Response(
            UserQuizAttemptDetailSerializer(attempt).data,
            status=status.HTTP_200_OK
        )
    
    @staticmethod
    def _grade_attempt(attempt):
        """Grade a quiz attempt"""
        answers = attempt.answers.all()
        total_points = 0
        earned_points = 0
        
        for answer in answers:
            question = answer.question
            total_points += question.points
            
            # Check if answer is correct
            is_correct = str(answer.user_answer).strip().lower() == str(question.correct_answer).strip().lower()
            answer.is_correct = is_correct
            
            if is_correct:
                answer.points_earned = question.points
                earned_points += question.points
            else:
                answer.points_earned = 0
            
            answer.save()
        
        if total_points > 0:
            score = (earned_points / total_points) * 100
        else:
            score = 0
        
        attempt.score = score
        attempt.total_points = total_points
        attempt.earned_points = earned_points
        attempt.is_passed = score >= attempt.quiz.passing_score
        attempt.status = 'graded'
        attempt.save()
    
    @action(detail=False, methods=['get'])
    def my_attempts(self, request):
        """Get all quiz attempts for the current user"""
        attempts = self.get_queryset().order_by('-start_time')
        serializer = UserQuizAttemptListSerializer(attempts, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def attempt_detail(self, request, pk=None):
        """Get detailed view of a specific attempt"""
        attempt = self.get_object()
        serializer = UserQuizAttemptDetailSerializer(attempt)
        return Response(serializer.data)
