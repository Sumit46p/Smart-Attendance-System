from django.contrib import admin
from .models import Attendance, QRToken


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'class_obj', 'attendance_date', 'status', 'marked_at')
    list_filter = ('status', 'attendance_date', 'class_obj')
    search_fields = ('student__name', 'student__email')


@admin.register(QRToken)
class QRTokenAdmin(admin.ModelAdmin):
    list_display = ('class_obj', 'token', 'created_at', 'expires_at')
