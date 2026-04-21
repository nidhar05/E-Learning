from django.db import models
from django.contrib.auth import get_user_model
from videos.models import Video

User = get_user_model()


class VideoNotes(models.Model):
    """AI-generated or instructor-created notes for a video"""
    
    video = models.OneToOneField(
        Video,
        on_delete=models.CASCADE,
        related_name='notes'
    )
    
    title = models.CharField(max_length=255)
    
    # Main notes content
    content = models.TextField()
    
    # Key takeaways
    key_takeaways = models.TextField(blank=True, null=True)
    
    # Important terms/glossary
    important_terms = models.TextField(blank=True, null=True)
    
    # Generated or manually created
    is_ai_generated = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Instructor who created or reviewed the notes"
    )
    
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notes for {self.video.title}"


class NoteSection(models.Model):
    """Structured sections within video notes"""
    
    notes = models.ForeignKey(
        VideoNotes,
        on_delete=models.CASCADE,
        related_name='sections'
    )
    
    title = models.CharField(max_length=255)
    content = models.TextField()
    order = models.IntegerField(default=0)
    
    # Optional properties
    icon = models.CharField(max_length=50, blank=True, null=True)  # For UI representation
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['notes', 'order']

    def __str__(self):
        return f"{self.notes.title} - {self.title}"


class NoteBookmark(models.Model):
    """User bookmarks specific sections or timestamps in notes"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='note_bookmarks'
    )
    
    notes = models.ForeignKey(
        VideoNotes,
        on_delete=models.CASCADE,
        related_name='bookmarks'
    )
    
    section = models.ForeignKey(
        NoteSection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookmarks'
    )
    
    title = models.CharField(max_length=255, blank=True)
    timestamp = models.IntegerField(blank=True, null=True)  # In seconds
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'notes', 'section']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.notes.title}"


class UserNoteProgress(models.Model):
    """Track user's progress through notes"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='note_progress'
    )
    
    notes = models.ForeignKey(
        VideoNotes,
        on_delete=models.CASCADE,
        related_name='user_progress'
    )
    
    # Progress tracking
    sections_read = models.IntegerField(default=0)
    last_read_section = models.ForeignKey(
        NoteSection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    progress_percentage = models.FloatField(default=0)  # 0-100
    
    is_completed = models.BooleanField(default=False)
    
    first_accessed = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'notes']
        ordering = ['-last_accessed']

    def __str__(self):
        return f"{self.user.username} - {self.notes.title} ({self.progress_percentage}%)"
