"""
Migración de datos: Fase 1 de jerarquía de categorías.

1. Las categorías de sistema existentes (planas) se convierten en grupos
   (parent=None — ya lo son, no hay cambio estructural).
2. Se agregan los grupos "Sin clasificar" (EXPENSE e INCOME) como grupos de sistema.
3. Las categorías de usuario existentes (sin parent) se mueven al grupo
   "Sin clasificar" del tipo correspondiente.
"""

from django.db import migrations


def seed_groups_and_move_orphans(apps, schema_editor):
    Category = apps.get_model("categories", "Category")

    # Crear grupos "Sin clasificar" si no existen
    for category_type in ("EXPENSE", "INCOME"):
        Category._default_manager.get_or_create(
            name="Sin clasificar",
            type=category_type,
            is_system=True,
            user=None,
            parent=None,
            defaults={
                "icon": "bi-question-circle",
                "color": "#adb5bd",
            },
        )

    # Mover categorías de usuario sin parent al grupo "Sin clasificar" correspondiente
    for category_type in ("EXPENSE", "INCOME"):
        sin_clasificar = Category._default_manager.get(
            name="Sin clasificar",
            type=category_type,
            is_system=True,
            user=None,
        )
        # Categorías de usuario sin parent (huérfanas)
        orphans = Category._default_manager.filter(
            is_system=False,
            parent=None,
            type=category_type,
        )
        orphans.update(parent=sin_clasificar)


def reverse_groups_and_move_orphans(apps, schema_editor):
    Category = apps.get_model("categories", "Category")

    # Desasignar parent de categorías de usuario
    Category._default_manager.filter(
        is_system=False,
        parent__isnull=False,
    ).update(parent=None)

    # Eliminar grupos "Sin clasificar"
    Category._default_manager.filter(
        name="Sin clasificar",
        is_system=True,
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("categories", "0007_add_parent_to_category"),
    ]

    operations = [
        migrations.RunPython(
            seed_groups_and_move_orphans,
            reverse_groups_and_move_orphans,
        ),
    ]
