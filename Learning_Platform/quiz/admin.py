from django import forms
from django.contrib import admin
from .models import Quiz, QuizQuestion, UserQuizAttempt, UserQuizAnswer


class QuizQuestionInline(admin.TabularInline):
    model = QuizQuestion
    extra = 1
    fields = ('question_type', 'question_text', 'correct_answer', 'order', 'points')


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'video', 'passing_score', 'max_attempts', 'is_published', 'generated_at')
    list_filter = ('is_published', 'generated_at', 'passing_score')
    search_fields = ('title', 'video__title', 'description')
    readonly_fields = ('generated_at', 'updated_at')
    inlines = [QuizQuestionInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('video', 'title', 'description', 'is_published')
        }),
        ('Quiz Settings', {
            'fields': ('passing_score', 'time_limit', 'max_attempts')
        }),
        ('Timestamps', {
            'fields': ('generated_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text_short', 'quiz', 'question_type', 'order', 'points', 'correct_answer')
    list_filter = ('question_type', 'quiz__title', 'points')
    search_fields = ('question_text', 'quiz__title')
    ordering = ('quiz', 'order')
    
    fieldsets = (
        ('Question Details', {
            'fields': ('quiz', 'question_type', 'question_text', 'order', 'points')
        }),
        ('Multiple Choice Options', {
            'fields': ('option_a', 'option_b', 'option_c', 'option_d'),
            'classes': ('collapse',)
        }),
        ('Answer & Explanation', {
            'fields': ('correct_answer', 'explanation')
        }),
    )
    
    def question_text_short(self, obj):
        return obj.question_text[:50] + '...' if len(obj.question_text) > 50 else obj.question_text
    question_text_short.short_description = 'Question'


@admin.register(UserQuizAttempt)
class UserQuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'attempt_number', 'score_display', 'is_passed', 'status', 'start_time')
    list_filter = ('is_passed', 'status', 'start_time', 'quiz__title')
    search_fields = ('user__username', 'user__email', 'quiz__title')
    readonly_fields = ('start_time', 'score', 'total_points', 'earned_points', 'is_passed', 'status')
    ordering = ('-start_time',)
    
    fieldsets = (
        ('User & Quiz', {
            'fields': ('user', 'quiz', 'attempt_number')
        }),
        ('Results', {
            'fields': ('score', 'total_points', 'earned_points', 'is_passed', 'status')
        }),
        ('Timeline', {
            'fields': ('start_time', 'end_time')
        }),
    )
    
    def score_display(self, obj):
        if obj.score is None:
            return '-'
        return f"{obj.score:.1f}%"
    score_display.short_description = 'Score'
    
    def has_add_permission(self, request):
        return False


@admin.register(UserQuizAnswer)
class UserQuizAnswerAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question_short', 'is_correct', 'points_earned')
    list_filter = ('is_correct', 'attempt__quiz__title')
    search_fields = ('attempt__user__username', 'question__question_text')
    readonly_fields = ('attempt', 'question', 'user_answer', 'is_correct', 'points_earned')
    
    def question_short(self, obj):
        return obj.question.question_text[:50] + '...' if len(obj.question.question_text) > 50 else obj.question.question_text
    question_short.short_description = 'Question'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

