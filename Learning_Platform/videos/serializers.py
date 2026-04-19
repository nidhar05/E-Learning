from rest_framework import serializers
from .models import Video


class VideoSerializer(serializers.ModelSerializer):
    video_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = [
            "id",
            "course",
            "title",
            "original_file",   
            "processed_file",
            "video_url",
            "duration",
            "order",
        ]

    def get_video_url(self, obj):
        request = self.context.get("request")

        if obj.original_file:
            return f"{request.scheme}://{request.get_host()}/api/videos/stream/{obj.original_file.name}"

        return None