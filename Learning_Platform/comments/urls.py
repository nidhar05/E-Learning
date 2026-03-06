from django.urls import path,include
from .views import CommentListCreateView

urlpatterns = [
    path('', CommentListCreateView.as_view(), name='comment-list-create'),
]