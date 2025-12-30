from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


# Register your models here.
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("email", "username", "default_currency", "is_active")
    list_filter = ("is_active", "default_currency")
    fieldsets = UserAdmin.fieldsets + (
        ("Preferencias", {"fields": ("default_currency", "alert_threshold")}),
    )
