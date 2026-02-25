from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsAdminOrTeacher
from .models import Class, Enrollment
from .serializers import ClassSerializer, EnrollmentSerializer


class ClassListCreateView(generics.ListCreateAPIView):
    """List all classes or create a new class."""
    serializer_class = ClassSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in ('admin', 'teacher'):
            if user.role == 'teacher':
                return Class.objects.filter(teacher=user)
            return Class.objects.all()
        # Students see only enrolled classes
        return Class.objects.filter(enrollments__student=user)

    def perform_create(self, serializer):
        if self.request.user.role == 'teacher':
            serializer.save(teacher=self.request.user)
        else:
            serializer.save()


class ClassDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete a class."""
    serializer_class = ClassSerializer
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    queryset = Class.objects.all()


class EnrollmentListCreateView(generics.ListCreateAPIView):
    """List enrollments or enroll a student."""
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Enrollment.objects.all()
        class_id = self.request.query_params.get('class_id')
        if class_id:
            queryset = queryset.filter(class_obj_id=class_id)
        if self.request.user.role == 'student':
            queryset = queryset.filter(student=self.request.user)
        return queryset


class EnrollmentDeleteView(generics.DestroyAPIView):
    """Remove an enrollment."""
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]
    queryset = Enrollment.objects.all()
