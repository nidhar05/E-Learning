from django.urls import path
from .views import MarkCompleteView, CourseProgressView, update_progress, MyLearningView

urlpatterns = [
    path('update/', update_progress, name='progress'),
    path('complete/<int:video_id>/', MarkCompleteView.as_view(), name='mark-complete'),
    path('<int:course_id>/',CourseProgressView.as_view(),name="course-progress"),
    path("my-learning/", MyLearningView.as_view(), name="my-learning"),
]