"""
Configuración del admin para ahorro.
"""

from django.contrib import admin

from .models import Saving, SavingMovement


class SavingMovementInline(admin.TabularInline):
    """
    Inline para movimientos de ahorro.

    Los movimientos son de solo lectura para proteger la integridad
    de current_amount. Los movimientos deben crearse solo a través
    de add_deposit() y add_withdrawal().
    """

    model = SavingMovement
    extra = 0
    readonly_fields = ("type", "amount", "description", "date", "created_at")
    fields = ("type", "amount", "description", "date", "created_at")
    can_delete = False
    ordering = ("-date", "-created_at")

    def has_add_permission(self, request, obj=None):
        """No permitir agregar movimientos desde admin."""
        return False

    def has_change_permission(self, request, obj=None):
        """No permitir editar movimientos desde admin."""
        return False


@admin.register(Saving)
class SavingAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "user",
        "formatted_current",
        "formatted_target",
        "progress_percentage",
        "status",
        "target_date",
        "is_active",
    )
    list_filter = (
        "status",
        "currency",
        "is_active",
        "target_date",
    )
    search_fields = (
        "name",
        "description",
        "user__email",
        "user__username",
    )
    ordering = ("-created_at",)

    readonly_fields = ("current_amount", "progress_percentage", "created_at", "updated_at")

    fieldsets = (
        ("Información Principal", {"fields": ("user", "name", "description")}),
        (
            "Montos",
            {"fields": ("target_amount", "current_amount", "currency", "progress_percentage")},
        ),
        ("Configuración", {"fields": ("target_date", "status", "icon", "color")}),
        ("Estado", {"fields": ("is_active", "deleted_at"), "classes": ("collapse",)}),
        ("Auditoría", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    inlines = [SavingMovementInline]

    def progress_percentage(self, obj):
        return f"{obj.progress_percentage}%"

    progress_percentage.short_description = "Progreso"


@admin.register(SavingMovement)
class SavingMovementAdmin(admin.ModelAdmin):
    """
    Admin para movimientos de ahorro.

    Solo lectura para proteger la integridad de los datos.
    """

    list_display = (
        "saving",
        "type",
        "formatted_amount",
        "description",
        "date",
        "created_at",
    )
    list_filter = (
        "type",
        "date",
        "saving__user",
    )
    search_fields = (
        "saving__name",
        "description",
    )
    ordering = ("-date", "-created_at")

    readonly_fields = (
        "saving",
        "type",
        "amount",
        "description",
        "date",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        """No permitir agregar movimientos desde admin."""
        return False

    def has_change_permission(self, request, obj=None):
        """No permitir editar movimientos desde admin."""
        return False

    def has_delete_permission(self, request, obj=None):
        """No permitir eliminar movimientos desde admin."""
        return False
