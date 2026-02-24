"""
URL configuration for Smart Attendance System.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/classes/', include('classes.urls')),
    path('api/attendance/', include('attendance.urls')),
]
