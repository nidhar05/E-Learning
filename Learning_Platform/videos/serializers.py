from django.conf import settings
from rest_framework import serializers
from .models import Video


class VideoSerializer(serializers.ModelSerializer):
    video_url = serializers.SerializerMethodField()
    subtitle_url = serializers.SerializerMethodField()
    subtitle_language = serializers.SerializerMethodField()
    subtitle_label = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = [
            "id",
            "course",
            "title",
            "original_file",   
            "processed_file",
            "video_url",
            "subtitle_file",
            "subtitle_url",
            "subtitle_language",
            "subtitle_label",
            "subtitle_text",
            "duration",
            "order",
        ]

    def get_video_url(self, obj):
        request = self.context.get("request")

        if obj.original_file:
            return f"{request.scheme}://{request.get_host()}/api/videos/stream/{obj.original_file.name}/"

        return None
    
    def get_subtitle_url(self, obj):
        request = self.context.get("request")
        
        if obj.subtitle_file:
            return f"{request.scheme}://{request.get_host()}/api/videos/stream/{obj.subtitle_file.name}/"
        
        return None

    def get_subtitle_language(self, obj):
        return getattr(settings, "SUBTITLE_TARGET_LANGUAGE", "en")

    def get_subtitle_label(self, obj):
        return getattr(settings, "SUBTITLE_TARGET_LABEL", "English")
