"""
Configuración del admin para notificaciones push.
"""

from django.contrib import admin

from .models import DeviceToken, Notification, RecurringReminderLog


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "platform", "is_active", "last_used_at", "created_at")
    list_filter = ("platform", "is_active")
    search_fields = ("user__email", "user__username", "token")
    ordering = ("-last_used_at",)
    readonly_fields = ("token", "created_at", "updated_at", "last_used_at")


@admin.register(RecurringReminderLog)
class RecurringReminderLogAdmin(admin.ModelAdmin):
    list_display = ("recurring", "due_date", "created_at")
    list_filter = ("due_date",)
    search_fields = ("recurring__name", "recurring__user__username")
    list_select_related = ("recurring", "recurring__user")
    readonly_fields = ("recurring", "due_date", "created_at", "updated_at")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "type", "title", "read_at", "created_at")
    list_filter = ("type",)
    search_fields = ("user__email", "user__username", "body")
    list_select_related = ("user",)
    readonly_fields = ("created_at", "updated_at")
