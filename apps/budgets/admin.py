"""
Configuración del admin para presupuestos.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import Budget


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = (
        "category",
        "period_display",
        "formatted_amount",
        "formatted_spent",
        "spent_percentage_display",
        "status_display",
        "user",
        "is_active",
    )
    list_filter = (
        "year",
        "month",
        "category",
        "user",
        "is_active",
    )
    search_fields = (
        "category__name",
        "user__email",
        "user__username",
        "notes",
    )
    ordering = ("-year", "-month", "category__name")

    readonly_fields = (
        "spent_amount",
        "remaining_amount",
        "spent_percentage",
        "status",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("Información Principal", {"fields": ("user", "category", "month", "year")}),
        ("Presupuesto", {"fields": ("amount", "alert_threshold", "notes")}),
        (
            "Estado Actual (Calculado)",
            {
                "fields": ("spent_amount", "remaining_amount", "spent_percentage", "status"),
                "classes": ("collapse",),
            },
        ),
        ("Estado", {"fields": ("is_active", "deleted_at"), "classes": ("collapse",)}),
        ("Auditoría", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def spent_percentage_display(self, obj):
        """Muestra el porcentaje gastado con barra de progreso."""
        percentage = obj.spent_percentage
        color = obj.status_class

        return format_html(
            '<div style="width:100px; background:#eee; border-radius:3px;">'
            '<div style="width:{}%; background:var(--bs-{}); height:20px; border-radius:3px; text-align:center; color:white; font-size:12px; line-height:20px;">'
            "{}%</div></div>",
            min(percentage, 100),
            color,
            percentage,
        )

    spent_percentage_display.short_description = "Progreso"

    def status_display(self, obj):
        """Muestra el estado con color."""
        status_labels = {"over": "🔴 Excedido", "warning": "🟡 Alerta", "ok": "🟢 OK"}
        return status_labels.get(obj.status, "Desconocido")

    status_display.short_description = "Estado"
