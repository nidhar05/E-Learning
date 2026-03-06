from django.shortcuts import render
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from .models import Video
from .serializers import VideoSerializer

class VideoListCreateView(generics.ListCreateAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):

        if self.request.user.role != "instructor":
            raise PermissionDenied("Only instructors can upload videos")

        serializer.save()