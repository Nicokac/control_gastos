"""Configuración del admin para ingresos."""

from django.contrib import admin

from .models import Income


# Register your models here.
@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "description",
        "formatted_amount",
        "category",
        "is_recurring",
        "user",
        "is_active",
    )
    list_filter = (
        "date",
        "category",
        "is_recurring",
        "currency",
        "is_active",
    )
    search_fields = (
        "description",
        "user__email",
        "user__username",
    )
    date_hierarchy = "date"
    ordering = ("-date", "-created_at")

    readonly_fields = ("amount_ars", "created_at", "updated_at")

    fieldsets = (
        ("Información Principal", {"fields": ("user", "date", "category", "description")}),
        ("Monto", {"fields": ("amount", "currency", "exchange_rate", "amount_ars")}),
        (
            "Detalles",
            {
                "fields": ("is_recurring",),
            },
        ),
        ("Estado", {"fields": ("is_active", "deleted_at"), "classes": ("collapse",)}),
        ("Auditoría", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def formatted_amount(self, obj):
        return obj.formatted_amount

    formatted_amount.short_description = "Monto"
