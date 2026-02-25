from django.urls import path
from .views import (
    ClassListCreateView,
    ClassDetailView,
    EnrollmentListCreateView,
    EnrollmentDeleteView,
)

urlpatterns = [
    path('', ClassListCreateView.as_view(), name='class_list_create'),
    path('<int:pk>/', ClassDetailView.as_view(), name='class_detail'),
    path('enrollments/', EnrollmentListCreateView.as_view(), name='enrollment_list_create'),
    path('enrollments/<int:pk>/', EnrollmentDeleteView.as_view(), name='enrollment_delete'),
]
