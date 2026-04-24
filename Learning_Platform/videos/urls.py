from django.urls import path

from .views import VideoDetailView, VideoListCreateView, stream_video


urlpatterns = [
    path("", VideoListCreateView.as_view()),
    path("<int:pk>/", VideoDetailView.as_view()),
    path("stream/<path:path>", stream_video),
    path("stream/<path:path>/", stream_video),
]
