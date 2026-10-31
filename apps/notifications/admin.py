"""
Configuración del admin para notificaciones push.
"""

from django.contrib import admin

from .models import DeviceToken


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "platform", "is_active", "last_used_at", "created_at")
    list_filter = ("platform", "is_active")
    search_fields = ("user__email", "user__username", "token")
    ordering = ("-last_used_at",)
    readonly_fields = ("token", "created_at", "updated_at", "last_used_at")
