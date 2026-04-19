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
            "video_url",
            "duration",
            "order",
        ]

    def get_video_url(self, obj):
        request = self.context.get("request")

        if obj.processed_file:
            return request.build_absolute_uri(
                f"stream/{obj.processed_file.name}"
            )
        elif obj.original_file:
            return request.build_absolute_uri(
                f"stream/{obj.original_file.name}"
            )

        return None