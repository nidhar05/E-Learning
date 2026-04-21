from rest_framework import serializers
from .models import VideoNotes, NoteSection, NoteBookmark, UserNoteProgress


class NoteSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoteSection
        fields = ['id', 'title', 'content', 'order', 'icon', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class VideoNotesListSerializer(serializers.ModelSerializer):
    section_count = serializers.SerializerMethodField()
    video_title = serializers.CharField(source='video.title', read_only=True)
    
    class Meta:
        model = VideoNotes
        fields = [
            'id', 'video', 'video_title', 'title', 'is_ai_generated',
            'is_published', 'section_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_section_count(self, obj):
        return obj.sections.count()


class VideoNotesDetailSerializer(serializers.ModelSerializer):
    sections = NoteSectionSerializer(many=True, read_only=True)
    video_title = serializers.CharField(source='video.title', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = VideoNotes
        fields = [
            'id', 'video', 'video_title', 'title', 'content', 'key_takeaways',
            'important_terms', 'is_ai_generated', 'is_published', 'sections',
            'created_by', 'created_by_username', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']


class NoteBookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoteBookmark
        fields = ['id', 'notes', 'section', 'title', 'timestamp', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserNoteProgressSerializer(serializers.ModelSerializer):
    notes_title = serializers.CharField(source='notes.title', read_only=True)
    last_read_section_title = serializers.CharField(
        source='last_read_section.title',
        read_only=True
    )
    
    class Meta:
        model = UserNoteProgress
        fields = [
            'id', 'notes', 'notes_title', 'sections_read', 'last_read_section',
            'last_read_section_title', 'progress_percentage', 'is_completed',
            'first_accessed', 'last_accessed'
        ]
        read_only_fields = ['id', 'first_accessed', 'last_accessed']
