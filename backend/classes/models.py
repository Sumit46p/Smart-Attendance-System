from django.db import models
from django.conf import settings


class Class(models.Model):
    subject_name = models.CharField(max_length=100)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='taught_classes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'classes'
        verbose_name_plural = 'classes'

    def __str__(self):
        return self.subject_name


class Enrollment(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    class_obj = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )

    class Meta:
        db_table = 'enrollments'
        unique_together = ('student', 'class_obj')

    def __str__(self):
        return f"{self.student.name} → {self.class_obj.subject_name}"
