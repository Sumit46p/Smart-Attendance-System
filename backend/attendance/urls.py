from django.urls import path
from .views import (
    GenerateQRView,
    ActiveQRView,
    ScanQRView,
    AttendanceListView,
    AttendanceStatsView,
    ExportAttendanceView,
    DashboardStatsView,
)

urlpatterns = [
    path('qr/generate/', GenerateQRView.as_view(), name='generate_qr'),
    path('qr/active/<int:class_id>/', ActiveQRView.as_view(), name='active_qr'),
    path('scan/', ScanQRView.as_view(), name='scan_qr'),
    path('list/', AttendanceListView.as_view(), name='attendance_list'),
    path('stats/', AttendanceStatsView.as_view(), name='attendance_stats'),
    path('export/', ExportAttendanceView.as_view(), name='export_attendance'),
    path('dashboard/', DashboardStatsView.as_view(), name='dashboard_stats'),
]
