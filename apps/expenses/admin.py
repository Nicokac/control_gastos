"""
Configuración del admin para gastos.
"""

from django.contrib import admin

from .models import Expense


# Register your models here.
@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "description",
        "formatted_amount",
        "category",
        "payment_method",
        "user",
    )
    list_filter = (
        "date",
        "category",
        "payment_method",
        "expense_type",
        "currency",
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
            "Detalles Opcionales",
            {"fields": ("payment_method", "expense_type"), "classes": ("collapse",)},
        ),
        ("Auditoría", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def formatted_amount(self, obj):
        return obj.formatted_amount

    formatted_amount.short_description = "Monto"
