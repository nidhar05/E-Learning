from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from .models import Course
from .serializers import CourseSerializer


# LIST + CREATE
class CourseListCreateView(generics.ListCreateAPIView):

    queryset = Course.objects.all()
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

    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_update(self, serializer):
        if self.request.user != serializer.instance.instructor:
            raise PermissionDenied("You can only edit your own courses.")
        serializer.save()

    def perform_destroy(self, instance):
        if self.request.user != instance.instructor:
            raise PermissionDenied("You can only delete your own courses.")
        instance.delete()
    
class ListCoursesView(generics.ListAPIView):
    
    queryset = Course.objects.all()
    serializer_class = CourseSerializer