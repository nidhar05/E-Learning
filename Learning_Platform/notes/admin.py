from django.contrib import admin
from .models import VideoNotes, NoteSection, NoteBookmark, UserNoteProgress


class NoteSectionInline(admin.TabularInline):
    model = NoteSection
    extra = 1
    fields = ('title', 'order', 'icon', 'created_at', 'updated_at')


@admin.register(VideoNotes)
class VideoNotesAdmin(admin.ModelAdmin):
    list_display = ('title', 'video', 'is_ai_generated', 'created_by', 'is_published', 'section_count', 'created_at')
    list_filter = ('is_ai_generated', 'is_published', 'created_at')
    search_fields = ('title', 'video__title', 'content')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [NoteSectionInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('video', 'title', 'is_ai_generated', 'created_by', 'is_published')
        }),
        ('Content', {
            'fields': ('content', 'key_takeaways', 'important_terms')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def section_count(self, obj):
        return obj.sections.count()
    section_count.short_description = 'Sections'


@admin.register(NoteSection)
class NoteSectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'notes', 'order', 'icon', 'content_preview', 'created_at')
    list_filter = ('notes__title', 'created_at')
    search_fields = ('title', 'content', 'notes__title')
    ordering = ('notes', 'order')
    
    fieldsets = (
        ('Section Details', {
            'fields': ('notes', 'title', 'order', 'icon')
        }),
        ('Content', {
            'fields': ('content',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'


@admin.register(NoteBookmark)
class NoteBookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'notes', 'section', 'title', 'timestamp', 'created_at')
    list_filter = ('created_at', 'user__username')
    search_fields = ('user__username', 'notes__title', 'title')
    ordering = ('-created_at',)
    
    def has_add_permission(self, request):
        return False


@admin.register(UserNoteProgress)
class UserNoteProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'notes', 'progress_bar', 'is_completed', 'last_accessed')
    list_filter = ('is_completed', 'last_accessed', 'notes__title')
    search_fields = ('user__username', 'notes__title')
    readonly_fields = ('first_accessed', 'last_accessed')
    
    fieldsets = (
        ('User & Notes', {
            'fields': ('user', 'notes')
        }),
        ('Progress', {
            'fields': ('sections_read', 'last_read_section', 'progress_percentage', 'is_completed')
        }),
        ('Timestamps', {
            'fields': ('first_accessed', 'last_accessed'),
            'classes': ('collapse',)
        }),
    )
    
    def progress_bar(self, obj):
        percentage = obj.progress_percentage
        filled = int(percentage / 10)
        empty = 10 - filled
        bar = '█' * filled + '░' * empty
        return f'{bar} {percentage:.0f}%'
    progress_bar.short_description = 'Progress'
    
    def has_add_permission(self, request):
        return False

