from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied

from .models import Course
from .serializers import CourseSerializer


# LIST + CREATE
class CourseListCreateView(generics.ListCreateAPIView):

    queryset = Course.objects.select_related('instructor').all()
    serializer_class = CourseSerializer

    def get_permissions(self):

        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):

        if self.request.user.role != 'instructor':
            raise PermissionDenied("Only instructors can create courses")

        serializer.save(instructor=self.request.user)


# RETRIEVE + UPDATE + DELETE
class CourseDetailView(generics.RetrieveUpdateDestroyAPIView):

    queryset = Course.objects.select_related('instructor').all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_update(self, serializer):
        if self.request.user.id != serializer.instance.instructor.id:
            raise PermissionDenied("You can only edit your own courses.")
        serializer.save()

    def perform_destroy(self, instance):
        if self.request.user.id != instance.instructor.id:
            raise PermissionDenied("You can only delete your own courses.")
        instance.delete()
    
class ListCoursesView(generics.ListAPIView):

    queryset = Course.objects.select_related('instructor').order_by('-created_at')
    serializer_class = CourseSerializer
    permission_classes = [permissions.AllowAny]


class InstructorCourseListView(generics.ListAPIView):

    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self.request.user, 'role', None) != 'instructor':
            return Course.objects.none()

        return Course.objects.select_related('instructor').filter(
            instructor=self.request.user
        ).order_by('-created_at')
