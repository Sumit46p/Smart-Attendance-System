from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Class, Enrollment

User = get_user_model()


class ClassSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)
    student_count = serializers.SerializerMethodField()

    class Meta:
        model = Class
        fields = ['id', 'subject_name', 'teacher', 'teacher_name', 'student_count', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_student_count(self, obj):
        return obj.enrollments.count()


class EnrollmentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    student_email = serializers.CharField(source='student.email', read_only=True)
    class_name = serializers.CharField(source='class_obj.subject_name', read_only=True)

    class Meta:
        model = Enrollment
        fields = ['id', 'student', 'student_name', 'student_email', 'class_obj', 'class_name']
        read_only_fields = ['id']
