from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Progress
from videos.models import Video

from rest_framework.views import APIView
from courses.models import Course
from .serializers import ProgressSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_progress(request):

    if request.user.role != "student":
        return Response(
            {"error": "Only students can update progress"},
            status=403
        )

    video_id = request.data.get("video_id")
    watch_time = request.data.get("watch_time")

    try:
        video = Video.objects.get(id=video_id)
    except Video.DoesNotExist:
        return Response(
            {"error": "Video not found"},
            status=404
        )

    progress, created = Progress.objects.get_or_create(
        user=request.user,
        video=video
    )

    progress.watch_time = watch_time
    progress.save()

    return Response({
        "message": "Progress updated",
        "watch_time": progress.watch_time
    })
    
class MarkCompleteView(APIView):
    
    permission_classes = [IsAuthenticated]

    def post(self, request, video_id):

        try:
            video = Video.objects.get(id=video_id)
        except Video.DoesNotExist:
            return Response(
                {"error": "Video not found"},
                status=404
            )

        progress, created = Progress.objects.get_or_create(
            user=request.user,
            video=video
        )

        progress.completed = True
        progress.save()

        return Response({
            "message": "Video marked as completed"
        })
        
class CourseProgressView(APIView):
    
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):

        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response(
                {"error": "Course not found"},
                status=404
            )

        total_videos = course.videos.count()

        completed_videos = Progress.objects.filter(
            user=request.user,
            video__course=course,
            completed=True
        ).count()

        if total_videos == 0:
            percentage = 0
        else:
            percentage = (completed_videos / total_videos) * 100

        return Response({
            "course": course.title,
            "total_videos": total_videos,
            "completed_videos": completed_videos,
            "progress_percentage": percentage
        })


class MyLearningView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        progress = Progress.objects.filter(
            user=request.user,
            completed=False,
            watch_time__gt=0
        ).order_by("-updated_at")

        serializer = ProgressSerializer(progress, many=True)

        return Response(serializer.data)