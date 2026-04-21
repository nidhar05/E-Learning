from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    QuizListView, QuizDetailView, QuizByVideoView, UserQuizAttemptViewSet
)

router = DefaultRouter()
router.register(r'attempts', UserQuizAttemptViewSet, basename='quiz-attempt')

urlpatterns = [
    path('', QuizListView.as_view(), name='quiz-list'),
    path('<int:pk>/', QuizDetailView.as_view(), name='quiz-detail'),
    path('video/<int:video_id>/', QuizByVideoView.as_view(), name='quiz-by-video'),
    path('', include(router.urls)),
]
