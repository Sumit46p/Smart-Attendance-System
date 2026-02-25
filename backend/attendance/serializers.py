from rest_framework import serializers
from .models import Attendance, QRToken


class QRTokenSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(source='class_obj.subject_name', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = QRToken
        fields = ['id', 'class_obj', 'class_name', 'token', 'created_at', 'expires_at', 'is_expired', 'latitude', 'longitude', 'radius_meters']
        read_only_fields = ['id', 'token', 'created_at', 'expires_at']


class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    student_email = serializers.CharField(source='student.email', read_only=True)
    class_name = serializers.CharField(source='class_obj.subject_name', read_only=True)

    class Meta:
        model = Attendance
        fields = [
            'id', 'student', 'student_name', 'student_email',
            'class_obj', 'class_name', 'attendance_date',
            'status', 'marked_at'
        ]
        read_only_fields = ['id', 'marked_at']


class ScanQRSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    device_id = serializers.CharField(required=False, allow_blank=True)
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)


class AttendanceStatsSerializer(serializers.Serializer):
    class_id = serializers.IntegerField()
    class_name = serializers.CharField()
    total_classes = serializers.IntegerField()
    present_count = serializers.IntegerField()
    absent_count = serializers.IntegerField()
    late_count = serializers.IntegerField()
    percentage = serializers.FloatField()
