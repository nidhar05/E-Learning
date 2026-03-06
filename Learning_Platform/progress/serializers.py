from rest_framework import serializers
from .models import Progress


class ProgressSerializer(serializers.ModelSerializer):

    video_title = serializers.CharField(source="video.title")
    course_title = serializers.CharField(source="video.course.title")
    
    class Meta:
        model = Progress
        fields = [
            "video",
            "video_title",
            "course_title",
            "watch_time",
            "completed"
        ]