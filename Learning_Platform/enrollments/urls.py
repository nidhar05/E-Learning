from django.urls import path
from .views import EnrollView, EnrollDetailView

urlpatterns = [
    path('enroll/<int:course_id>/', EnrollView.as_view(), name='enroll'),
    path('', EnrollDetailView.as_view(), name='enrollment-detail'),
]