from django.contrib import admin
from .models import Class, Enrollment


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('subject_name', 'teacher', 'created_at')
    list_filter = ('teacher',)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'class_obj')
