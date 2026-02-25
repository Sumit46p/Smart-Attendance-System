import csv
import math
from datetime import date

from django.http import HttpResponse
from django.db.models import Count, Q
from django.conf import settings as django_settings
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsAdminOrTeacher, IsStudent
from classes.models import Class, Enrollment
from .models import Attendance, QRToken
from .serializers import (
    AttendanceSerializer,
    QRTokenSerializer,
    ScanQRSerializer,
    AttendanceStatsSerializer,
)

# Late threshold in seconds (configurable in settings, default 15 min)
LATE_THRESHOLD_SECONDS = getattr(django_settings, 'LATE_THRESHOLD_SECONDS', 900)


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in meters between two GPS coordinates."""
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


class GenerateQRView(APIView):
    """Generate a dynamic QR token for a class (teacher/admin only)."""
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]

    def post(self, request):
        class_id = request.data.get('class_id')
        if not class_id:
            return Response({'error': 'class_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            class_obj = Class.objects.get(id=class_id)
        except Class.DoesNotExist:
            return Response({'error': 'Class not found'}, status=status.HTTP_404_NOT_FOUND)

        # Invalidate old tokens for this class
        QRToken.objects.filter(class_obj=class_obj).delete()

        # Create QR with optional geofence
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        radius_meters = request.data.get('radius_meters', 100)

        qr_token = QRToken.objects.create(
            class_obj=class_obj,
            created_by=request.user,
            latitude=float(latitude) if latitude else None,
            longitude=float(longitude) if longitude else None,
            radius_meters=int(radius_meters),
        )
        serializer = QRTokenSerializer(qr_token)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ActiveQRView(APIView):
    """Get the active (non-expired) QR token for a class."""
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]

    def get(self, request, class_id):
        try:
            qr_token = QRToken.objects.filter(
                class_obj_id=class_id,
                expires_at__gt=timezone.now()
            ).latest('created_at')
            return Response(QRTokenSerializer(qr_token).data)
        except QRToken.DoesNotExist:
            return Response({'error': 'No active QR token'}, status=status.HTTP_404_NOT_FOUND)


class ScanQRView(APIView):
    """Student scans QR code to mark attendance."""
    permission_classes = [IsAuthenticated, IsStudent]

    def post(self, request):
        serializer = ScanQRSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data['token']
        device_id = serializer.validated_data.get('device_id', '')
        latitude = serializer.validated_data.get('latitude')
        longitude = serializer.validated_data.get('longitude')

        # 1. Validate token
        try:
            qr_token = QRToken.objects.get(token=token)
        except QRToken.DoesNotExist:
            return Response({'error': 'Invalid QR code'}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Check expiry
        if qr_token.is_expired:
            return Response({'error': 'QR code has expired. Ask teacher to generate a new one.'}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Check enrollment
        class_obj = qr_token.class_obj
        if not Enrollment.objects.filter(student=request.user, class_obj=class_obj).exists():
            return Response({'error': 'You are not enrolled in this class'}, status=status.HTTP_403_FORBIDDEN)

        # 4. Check duplicate attendance
        today = date.today()
        if Attendance.objects.filter(student=request.user, class_obj=class_obj, attendance_date=today).exists():
            return Response({'error': 'Attendance already marked for today'}, status=status.HTTP_400_BAD_REQUEST)

        # 5. Check for device reuse (anti-proxy)
        if device_id:
            existing_device = Attendance.objects.filter(
                class_obj=class_obj,
                attendance_date=today,
                device_id=device_id
            ).exclude(student=request.user).first()
            if existing_device:
                return Response(
                    {'error': 'This device was already used to mark attendance for another student. Proxy attendance is not allowed.'},
                    status=status.HTTP_403_FORBIDDEN
                )

        # 6. Geofence check — if teacher set a location, verify student is within radius
        if qr_token.latitude is not None and qr_token.longitude is not None:
            if latitude is None or longitude is None:
                return Response(
                    {'error': 'Location access is required. Please enable GPS and try again.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            distance = haversine_distance(qr_token.latitude, qr_token.longitude, latitude, longitude)
            if distance > qr_token.radius_meters:
                return Response(
                    {'error': f'You are {int(distance)}m away from the classroom. You must be within {qr_token.radius_meters}m to mark attendance.'},
                    status=status.HTTP_403_FORBIDDEN
                )

        # 7. Get client IP
        ip_address = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or request.META.get('REMOTE_ADDR')

        # 8. Determine late status
        time_diff = (timezone.now() - qr_token.created_at).total_seconds()
        late_threshold_min = LATE_THRESHOLD_SECONDS / 60
        attendance_status = 'late' if time_diff > LATE_THRESHOLD_SECONDS else 'present'

        # 9. Create attendance
        attendance = Attendance.objects.create(
            student=request.user,
            class_obj=class_obj,
            attendance_date=today,
            status=attendance_status,
            device_id=device_id,
            ip_address=ip_address,
            latitude=latitude,
            longitude=longitude,
        )

        # Build response with late criteria info
        response_data = {
            'message': f'Attendance marked as {attendance_status}!',
            'attendance': AttendanceSerializer(attendance).data,
            'late_criteria': {
                'threshold_minutes': late_threshold_min,
                'scanned_after_seconds': int(time_diff),
                'was_late': attendance_status == 'late',
                'explanation': f'Students scanning after {int(late_threshold_min)} minutes from QR generation are marked late. You scanned after {int(time_diff // 60)} min {int(time_diff % 60)} sec.'
            }
        }

        if qr_token.latitude is not None:
            distance = haversine_distance(qr_token.latitude, qr_token.longitude, latitude, longitude) if latitude else 0
            response_data['location_check'] = {
                'allowed_radius_meters': qr_token.radius_meters,
                'your_distance_meters': int(distance),
                'passed': True
            }

        return Response(response_data, status=status.HTTP_201_CREATED)


class AttendanceListView(generics.ListAPIView):
    """List attendance records with filtering."""
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Attendance.objects.all().order_by('-attendance_date', '-marked_at')

        if user.role == 'student':
            queryset = queryset.filter(student=user)
        elif user.role == 'teacher':
            queryset = queryset.filter(class_obj__teacher=user)

        # Filters
        class_id = self.request.query_params.get('class_id')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        student_id = self.request.query_params.get('student_id')
        status_filter = self.request.query_params.get('status')

        if class_id:
            queryset = queryset.filter(class_obj_id=class_id)
        if date_from:
            queryset = queryset.filter(attendance_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(attendance_date__lte=date_to)
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset


class AttendanceStatsView(APIView):
    """Get attendance statistics for a student."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        student_id = request.query_params.get('student_id', request.user.id)
        if request.user.role == 'student':
            student_id = request.user.id

        enrollments = Enrollment.objects.filter(student_id=student_id).select_related('class_obj')
        stats = []

        for enrollment in enrollments:
            class_obj = enrollment.class_obj
            attendance_records = Attendance.objects.filter(
                student_id=student_id,
                class_obj=class_obj
            )
            total = attendance_records.count()
            present = attendance_records.filter(status='present').count()
            absent = attendance_records.filter(status='absent').count()
            late = attendance_records.filter(status='late').count()

            total_class_dates = Attendance.objects.filter(
                class_obj=class_obj
            ).values('attendance_date').distinct().count()

            percentage = (present + late) / total_class_dates * 100 if total_class_dates > 0 else 0

            stats.append({
                'class_id': class_obj.id,
                'class_name': class_obj.subject_name,
                'total_classes': total_class_dates,
                'present_count': present,
                'absent_count': absent,
                'late_count': late,
                'percentage': round(percentage, 2),
            })

        return Response(stats)


class ExportAttendanceView(APIView):
    """Export attendance as CSV."""
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]

    def get(self, request):
        class_id = request.query_params.get('class_id')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        queryset = Attendance.objects.all().order_by('attendance_date', 'student__name')

        if request.user.role == 'teacher':
            queryset = queryset.filter(class_obj__teacher=request.user)
        if class_id:
            queryset = queryset.filter(class_obj_id=class_id)
        if date_from:
            queryset = queryset.filter(attendance_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(attendance_date__lte=date_to)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="attendance_report.csv"'

        writer = csv.writer(response)
        writer.writerow(['Student Name', 'Email', 'Class', 'Date', 'Status', 'Marked At'])

        for record in queryset.select_related('student', 'class_obj'):
            writer.writerow([
                record.student.name,
                record.student.email,
                record.class_obj.subject_name,
                record.attendance_date,
                record.status,
                record.marked_at.strftime('%Y-%m-%d %H:%M:%S'),
            ])

        return response


class DashboardStatsView(APIView):
    """Dashboard statistics for admin/teacher."""
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]

    def get(self, request):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        if request.user.role == 'teacher':
            classes = Class.objects.filter(teacher=request.user)
        else:
            classes = Class.objects.all()

        today = date.today()
        today_attendance = Attendance.objects.filter(
            attendance_date=today,
            class_obj__in=classes
        )

        total_students = User.objects.filter(role='student').count()
        total_classes = classes.count()
        today_present = today_attendance.filter(status='present').count()
        today_late = today_attendance.filter(status='late').count()
        today_absent = today_attendance.filter(status='absent').count()

        return Response({
            'total_students': total_students,
            'total_classes': total_classes,
            'today_present': today_present,
            'today_late': today_late,
            'today_absent': today_absent,
            'today_total': today_present + today_late + today_absent,
        })
