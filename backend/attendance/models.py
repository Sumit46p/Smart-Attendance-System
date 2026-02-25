import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class QRToken(models.Model):
    """Dynamic QR token that expires after configured seconds."""
    class_obj = models.ForeignKey(
        'classes.Class',
        on_delete=models.CASCADE,
        related_name='qr_tokens'
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    # Geofencing — teacher sets location when generating QR
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    radius_meters = models.IntegerField(default=100, help_text="Allowed radius in meters from QR location")

    class Meta:
        db_table = 'qr_tokens'

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(
                seconds=settings.QR_EXPIRY_SECONDS
            )
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"QR:{self.class_obj.subject_name} ({self.token})"


class Attendance(models.Model):
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attendances'
    )
    class_obj = models.ForeignKey(
        'classes.Class',
        on_delete=models.CASCADE,
        related_name='attendances'
    )
    attendance_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    device_id = models.CharField(max_length=255, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    marked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'attendance'
        unique_together = ('student', 'class_obj', 'attendance_date')
        indexes = [
            models.Index(fields=['student'], name='idx_attendance_student'),
            models.Index(fields=['class_obj'], name='idx_attendance_class'),
            models.Index(fields=['attendance_date'], name='idx_attendance_date'),
        ]

    def __str__(self):
        return f"{self.student.name} - {self.class_obj.subject_name} - {self.attendance_date}"
