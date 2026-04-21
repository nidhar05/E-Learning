from rest_framework import serializers
from .models import Quiz, QuizQuestion, UserQuizAttempt, UserQuizAnswer


class QuizQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizQuestion
        fields = [
            'id', 'question_type', 'question_text', 'option_a', 'option_b',
            'option_c', 'option_d', 'explanation', 'order', 'points'
        ]
        read_only_fields = ['id']


class QuizDetailSerializer(serializers.ModelSerializer):
    questions = QuizQuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Quiz
        fields = [
            'id', 'title', 'description', 'passing_score', 'time_limit',
            'max_attempts', 'is_published', 'questions', 'generated_at'
        ]
        read_only_fields = ['id', 'generated_at']


class QuizListSerializer(serializers.ModelSerializer):
    question_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Quiz
        fields = [
            'id', 'title', 'description', 'passing_score', 'max_attempts',
            'question_count', 'is_published', 'generated_at'
        ]
        read_only_fields = ['id', 'generated_at']
    
    def get_question_count(self, obj):
        return obj.questions.count()


class UserQuizAnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.question_text', read_only=True)
    correct_answer = serializers.CharField(source='question.correct_answer', read_only=True)
    
    class Meta:
        model = UserQuizAnswer
        fields = [
            'id', 'question', 'question_text', 'user_answer', 'correct_answer',
            'is_correct', 'points_earned'
        ]


class UserQuizAttemptDetailSerializer(serializers.ModelSerializer):
    answers = UserQuizAnswerSerializer(many=True, read_only=True)
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    
    class Meta:
        model = UserQuizAttempt
        fields = [
            'id', 'quiz', 'quiz_title', 'attempt_number', 'start_time',
            'end_time', 'score', 'total_points', 'earned_points',
            'is_passed', 'status', 'answers'
        ]
        read_only_fields = ['id', 'start_time', 'score', 'is_passed', 'status']


class UserQuizAttemptListSerializer(serializers.ModelSerializer):
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    
    class Meta:
        model = UserQuizAttempt
        fields = [
            'id', 'quiz', 'quiz_title', 'attempt_number', 'start_time',
            'end_time', 'score', 'is_passed', 'status'
        ]
        read_only_fields = ['id', 'start_time', 'score', 'is_passed', 'status']
