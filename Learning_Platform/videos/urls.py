from django.urls import path
from .views import VideoListCreateView, VideoDetailView, stream_video

urlpatterns = [
    path("", VideoListCreateView.as_view()),                 # /api/videos/
    path("<int:pk>/", VideoDetailView.as_view()),           # /api/videos/1/
    
    # 🔥 REQUIRED FOR VIDEO PLAYBACK
    path("stream/<path:path>/", stream_video),              # /api/videos/stream/...
]