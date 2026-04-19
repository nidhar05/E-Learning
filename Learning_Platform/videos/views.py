import os
from django.conf import settings
from django.http import StreamingHttpResponse, Http404

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.exceptions import PermissionDenied

from .models import Video
from .serializers import VideoSerializer


# ✅ LIST + CREATE
class VideoListCreateView(generics.ListCreateAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        return {"request": self.request}

    def perform_create(self, serializer):
        if self.request.user.role != "instructor":
            raise PermissionDenied("Only instructors can upload videos")

        course = serializer.validated_data["course"]

        if self.request.user != course.instructor:
            raise PermissionDenied("You can only upload to your course")

        serializer.save()


# ✅ DETAIL
class VideoDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_destroy(self, instance):
        if self.request.user != instance.course.instructor:
            raise PermissionDenied("You can delete only your videos")

        instance.delete()


# ✅ STREAM (VERY IMPORTANT 🔥)
def stream_video(request, path):
    file_path = os.path.join(settings.MEDIA_ROOT, path)

    if not os.path.exists(file_path):
        raise Http404("Video not found")

    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("Range", None)

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
            content_type="video/mp4",
        )

        response["Content-Range"] = f"bytes {start}-{end}/{file_size}"
        response["Accept-Ranges"] = "bytes"
        response["Content-Length"] = str(chunk_size)

        return response

    return StreamingHttpResponse(
        open(file_path, "rb"),
        content_type="video/mp4"
    )