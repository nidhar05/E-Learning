from django.shortcuts import get_object_or_404
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.exceptions import PermissionDenied, ValidationError

from videos.models import Video
from .models import VideoNotes, NoteSection, NoteBookmark, UserNoteProgress
from .serializers import (
    VideoNotesListSerializer, VideoNotesDetailSerializer, NoteSectionSerializer,
    NoteBookmarkSerializer, UserNoteProgressSerializer
)


def auto_create_notes(video):
    """Auto-create notes and sections if they don't exist"""
    notes, created = VideoNotes.objects.get_or_create(
        video=video,
        defaults={
            'title': f"Notes: {video.title}",
            'content': f"Notes for video: {video.title}\n\nAdd comprehensive notes here.",
            'key_takeaways': "Key takeaways:\n• Point 1\n• Point 2\n• Point 3",
            'important_terms': "Glossary:\nTerm 1: Definition\nTerm 2: Definition",
            'is_ai_generated': True,
            'is_published': True
        }
    )
    
    if created and not notes.sections.exists():
        NoteSection.objects.create(
            notes=notes,
            title="Introduction",
            content="Overview of the main concepts",
            order=1
        )
    
    return notes
from .serializers import (
    VideoNotesListSerializer, VideoNotesDetailSerializer, NoteSectionSerializer,
    NoteBookmarkSerializer, UserNoteProgressSerializer
)


class VideoNotesListView(generics.ListCreateAPIView):
    """List video notes or create new notes (instructor only)"""
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        return VideoNotes.objects.filter(is_published=True)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return VideoNotesDetailSerializer
        return VideoNotesListSerializer
    
    def perform_create(self, serializer):
        if self.request.user.role != 'instructor':
            raise PermissionDenied("Only instructors can create notes")
        
        video = serializer.validated_data.get('video')
        if video.course.instructor != self.request.user:
            raise PermissionDenied("You can only create notes for your videos")
        
        serializer.save(created_by=self.request.user)


class VideoNotesDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete video notes"""
    queryset = VideoNotes.objects.all()
    serializer_class = VideoNotesDetailSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def perform_update(self, serializer):
        if self.request.user.role != 'instructor':
            raise PermissionDenied("Only instructors can update notes")
        
        if self.get_object().video.course.instructor != self.request.user:
            raise PermissionDenied("You can only update your notes")
        
        serializer.save()
    
    def perform_destroy(self, instance):
        if self.request.user.role != 'instructor':
            raise PermissionDenied("Only instructors can delete notes")
        
        if instance.video.course.instructor != self.request.user:
            raise PermissionDenied("You can only delete your notes")
        
        instance.delete()


class NotesByVideoView(generics.RetrieveAPIView):
    """Get notes for a specific video - auto-creates if not exists"""
    serializer_class = VideoNotesDetailSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_object(self):
        video_id = self.kwargs.get('video_id')
        video = get_object_or_404(Video, pk=video_id)
        # Auto-create notes if they don't exist
        return auto_create_notes(video)


class NoteSectionViewSet(viewsets.ModelViewSet):
    """Manage note sections"""
    serializer_class = NoteSectionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        notes_id = self.kwargs.get('notes_id')
        return NoteSection.objects.filter(notes_id=notes_id)
    
    def perform_create(self, serializer):
        notes_id = self.kwargs.get('notes_id')
        notes = get_object_or_404(VideoNotes, pk=notes_id)
        
        if notes.created_by != self.request.user and self.request.user.role != 'admin':
            raise PermissionDenied("You can only add sections to your notes")
        
        serializer.save(notes=notes)
    
    def perform_update(self, serializer):
        notes = serializer.instance.notes
        
        if notes.created_by != self.request.user and self.request.user.role != 'admin':
            raise PermissionDenied("You can only update your notes sections")
        
        serializer.save()


class NoteBookmarkViewSet(viewsets.ModelViewSet):
    """Manage user bookmarks in notes"""
    serializer_class = NoteBookmarkSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return NoteBookmark.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def add_bookmark(self, request):
        """Add a bookmark to a specific section"""
        notes_id = request.data.get('notes_id')
        section_id = request.data.get('section_id')
        title = request.data.get('title', '')
        timestamp = request.data.get('timestamp')
        
        notes = get_object_or_404(VideoNotes, pk=notes_id)
        section = get_object_or_404(NoteSection, pk=section_id, notes=notes) if section_id else None
        
        bookmark, created = NoteBookmark.objects.update_or_create(
            user=request.user,
            notes=notes,
            section=section,
            defaults={'title': title, 'timestamp': timestamp}
        )
        
        serializer = NoteBookmarkSerializer(bookmark)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(serializer.data, status=status_code)
    
    @action(detail=False, methods=['get'])
    def my_bookmarks(self, request):
        """Get all bookmarks for current user"""
        bookmarks = self.get_queryset().order_by('-created_at')
        serializer = NoteBookmarkSerializer(bookmarks, many=True)
        return Response(serializer.data)


class UserNoteProgressViewSet(viewsets.ModelViewSet):
    """Track and manage user progress through notes"""
    serializer_class = UserNoteProgressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserNoteProgress.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def track_progress(self, request):
        """Update user's progress through notes"""
        notes_id = request.data.get('notes_id')
        section_id = request.data.get('section_id')
        progress_percentage = request.data.get('progress_percentage', 0)
        
        notes = get_object_or_404(VideoNotes, pk=notes_id)
        section = get_object_or_404(NoteSection, pk=section_id) if section_id else None
        
        progress, created = UserNoteProgress.objects.update_or_create(
            user=request.user,
            notes=notes,
            defaults={
                'last_read_section': section,
                'progress_percentage': min(progress_percentage, 100),
                'is_completed': progress_percentage >= 100
            }
        )
        
        serializer = UserNoteProgressSerializer(progress)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def my_progress(self, request):
        """Get all user progress through notes"""
        progress = self.get_queryset().order_by('-last_accessed')
        serializer = UserNoteProgressSerializer(progress, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_section_read(self, request):
        """Mark a section as read and update progress"""
        notes_id = request.data.get('notes_id')
        section_id = request.data.get('section_id')
        
        notes = get_object_or_404(VideoNotes, pk=notes_id)
        section = get_object_or_404(NoteSection, pk=section_id)
        
        if section.notes != notes:
            raise ValidationError("Section does not belong to this notes")
        
        progress, _ = UserNoteProgress.objects.get_or_create(
            user=request.user,
            notes=notes
        )
        
        # Update sections read count and last read section
        if progress.last_read_section != section:
            progress.sections_read = NoteSection.objects.filter(
                notes=notes,
                id__lte=section.id
            ).count()
            progress.last_read_section = section
        
        # Calculate progress percentage
        total_sections = notes.sections.count()
        if total_sections > 0:
            progress.progress_percentage = (progress.sections_read / total_sections) * 100
        
        progress.save()
        
        serializer = UserNoteProgressSerializer(progress)
        return Response(serializer.data, status=status.HTTP_200_OK)
