from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    VideoNotesListView, VideoNotesDetailView, NotesByVideoView,
    NoteSectionViewSet, NoteBookmarkViewSet, UserNoteProgressViewSet
)

router = DefaultRouter()
router.register(r'bookmarks', NoteBookmarkViewSet, basename='note-bookmark')
router.register(r'progress', UserNoteProgressViewSet, basename='note-progress')

urlpatterns = [
    path('', VideoNotesListView.as_view(), name='notes-list'),
    path('<int:pk>/', VideoNotesDetailView.as_view(), name='notes-detail'),
    path('video/<int:video_id>/', NotesByVideoView.as_view(), name='notes-by-video'),
    path('<int:notes_id>/sections/', NoteSectionViewSet.as_view({'get': 'list', 'post': 'create'}), name='notes-sections-list'),
    path('<int:notes_id>/sections/<int:pk>/', NoteSectionViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='notes-sections-detail'),
    path('', include(router.urls)),
]
