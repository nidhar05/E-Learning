import os
import math
from django.conf import settings
from django.http import StreamingHttpResponse, Http404
import mimetypes

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.exceptions import PermissionDenied

from .models import Video
from .serializers import VideoSerializer
from .signals import schedule_video_processing
from .utils.audio_utils import get_media_duration


# ✅ LIST + CREATE
class VideoListCreateView(generics.ListCreateAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Video.objects.all().order_by("course_id", "order", "id")
        user = self.request.user

        if user.role == "instructor":
            queryset = queryset.filter(course__instructor=user)

        course_id = self.request.query_params.get("course_id")
        if course_id:
            queryset = queryset.filter(course_id=course_id)

        return queryset

    def get_serializer_context(self):
        return {"request": self.request}

    def perform_create(self, serializer):
        if self.request.user.role != "instructor":
            raise PermissionDenied("Only instructors can upload videos")

        course = serializer.validated_data["course"]

        if self.request.user != course.instructor:
            raise PermissionDenied("You can only upload to your course")

        video = serializer.save()

        if not video.duration and video.original_file:
            video_path = os.path.join(settings.MEDIA_ROOT, video.original_file.name)
            try:
                duration_seconds = get_media_duration(video_path)
                video.duration = max(1, math.ceil(duration_seconds / 60))
                video.save(update_fields=["duration"])
            except Exception:
                pass


# ✅ DETAIL
class VideoDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self):
        return super().get_object()

    def perform_destroy(self, instance):
        if self.request.user != instance.course.instructor:
            raise PermissionDenied("You can delete only your videos")

        instance.delete()

    def perform_update(self, serializer):
        instance = self.get_object()

        if self.request.user != instance.course.instructor:
            raise PermissionDenied("You can update only your videos")

        video = serializer.save()
        schedule_video_processing(video.id)


# ✅ STREAM (VERY IMPORTANT 🔥)
def stream_video(request, path):
    path = (path or "").rstrip("/\\")
    file_path = os.path.join(settings.MEDIA_ROOT, path)

    if not os.path.exists(file_path):
        raise Http404("Video not found")

    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("Range", None)
    content_type, _ = mimetypes.guess_type(file_path)
    content_type = content_type or "application/octet-stream"

    if range_header:
        start, end = range_header.replace("bytes=", "").split("-")
        start = int(start)
        end = int(end) if end else file_size - 1

        chunk_size = end - start + 1

        def file_iterator(file, start, length):
            file.seek(start)
            remaining = length
            while remaining > 0:
                chunk = file.read(min(8192, remaining))
                if not chunk:
                    break
                yield chunk
                remaining -= len(chunk)

        response = StreamingHttpResponse(
            file_iterator(open(file_path, "rb"), start, chunk_size),
            status=206,
            content_type=content_type,
        )

        response["Content-Range"] = f"bytes {start}-{end}/{file_size}"
        response["Accept-Ranges"] = "bytes"
        response["Content-Length"] = str(chunk_size)
        response["Access-Control-Allow-Origin"] = "*"
        response["X-Content-Type-Options"] = "nosniff"
        response["Content-Disposition"] = "inline"

        return response

    response = StreamingHttpResponse(
        open(file_path, "rb"),
        content_type=content_type,
    )
    response["Accept-Ranges"] = "bytes"
    response["Content-Length"] = str(file_size)
    response["Access-Control-Allow-Origin"] = "*"
    response["X-Content-Type-Options"] = "nosniff"
    response["Content-Disposition"] = "inline"
    return response
