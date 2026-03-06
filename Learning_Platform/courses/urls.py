from django.urls import path
from .views import CourseListCreateView, CourseDetailView, ListCoursesView

urlpatterns = [
    path('', ListCoursesView.as_view(), name='list-courses'),
    path('create/', CourseListCreateView.as_view(), name='create-course'),
    path('<int:pk>/', CourseDetailView.as_view(), name='update-course'), 
]