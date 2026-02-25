from django.contrib import admin
from django.contrib.auth import get_user_model

User = get_user_model()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active')
    search_fields = ('name', 'email')
