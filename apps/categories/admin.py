"""
Configuración del admin para categorías.
"""

from django.contrib import admin
from .models import Category

# Register your models here.
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'type',
        'is_system',
        'user',
        'icon',
        'color',
        'is_active',
        'created_at'
    )
    list_filter = ('type', 'is_system', 'is_active')
    search_fields = ('name', 'user__email')
    ordering = ('type', 'name')

    fieldsets = (
        (None, {
            'fields': ('name', 'type')
        }),
        ('Configuración', {
            'fields': ('is_system', 'user', 'icon', 'color')
        }),
        ('Estado', {
            'fields': ('is_active',),
            'classes': ('collapse',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """Las categorías del sistema no se pueden editar."""
        if obj and obj.is_system:
            return ('name', 'type', 'is_system', 'user', 'icon', 'color')
        return()