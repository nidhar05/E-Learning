from django.db import models
from django.contrib.auth import get_user_model
from videos.models import Video

User = get_user_model()


class Quiz(models.Model):
    """Quiz generated from video content"""
    video = models.OneToOneField(
        Video,
        on_delete=models.CASCADE,
        related_name='quiz'
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    # AI-generated or instructor-created
    generated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Quiz settings
    passing_score = models.IntegerField(default=70)  # Percentage
    time_limit = models.IntegerField(blank=True, null=True)  # In minutes
    max_attempts = models.IntegerField(default=3)
    
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['-generated_at']

    def __str__(self):
        return self.title


class QuizQuestion(models.Model):
    """Individual questions in a quiz"""
    
    QUESTION_TYPE_CHOICES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
        ('essay', 'Essay'),
    ]

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPE_CHOICES,
        default='multiple_choice'
    )
    
    question_text = models.TextField()
    
    # For multiple_choice and true_false questions
    option_a = models.CharField(max_length=500, blank=True, null=True)
    option_b = models.CharField(max_length=500, blank=True, null=True)
    option_c = models.CharField(max_length=500, blank=True, null=True)
    option_d = models.CharField(max_length=500, blank=True, null=True)
    
    # Correct answer (A, B, C, D for multiple choice; True/False for true_false)
    correct_answer = models.CharField(max_length=100)
    
    # Explanation for the correct answer
    explanation = models.TextField(blank=True, null=True)
    
    # Question order in the quiz
    order = models.IntegerField(default=0)
    
    # Points for this question
    points = models.IntegerField(default=1)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['quiz', 'order']

    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}"


class UserQuizAttempt(models.Model):
    """Track user attempts on a quiz"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='quiz_attempts'
    )
    
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='user_attempts'
    )
    
    attempt_number = models.IntegerField()
    
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(blank=True, null=True)
    
    score = models.FloatField(blank=True, null=True)  # Percentage
    total_points = models.FloatField(blank=True, null=True)
    earned_points = models.FloatField(blank=True, null=True)
    
    is_passed = models.BooleanField(default=False)
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('in_progress', 'In Progress'),
            ('submitted', 'Submitted'),
            ('graded', 'Graded'),
        ],
        default='in_progress'
    )

    class Meta:
        unique_together = ['user', 'quiz', 'attempt_number']
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} (Attempt {self.attempt_number})"


class UserQuizAnswer(models.Model):
    """User's answer to a specific quiz question"""
    
    attempt = models.ForeignKey(
        UserQuizAttempt,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    
    question = models.ForeignKey(
        QuizQuestion,
        on_delete=models.CASCADE,
        related_name='user_answers'
    )
    
    user_answer = models.TextField()  # User's response
    
    points_earned = models.FloatField(default=0)
    
    is_correct = models.BooleanField(blank=True, null=True)
    
    answered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.attempt.user.username} - Q{self.question.order}"
