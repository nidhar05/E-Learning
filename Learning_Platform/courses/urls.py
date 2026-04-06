from django.urls import path

from .views import (
    CourseDetailView,
    CourseListCreateView,
    InstructorCourseListView,
    ListCoursesView,
)

urlpatterns = [
    path('', ListCoursesView.as_view(), name='list-courses'),
    path('my-courses/', InstructorCourseListView.as_view(), name='my-courses'),
    path('create/', CourseListCreateView.as_view(), name='create-course'),
    path('<int:pk>/', CourseDetailView.as_view(), name='update-course'), 
]
