"""
Migración de datos: agrega una subcategoría de sistema por defecto dentro
de cada grupo "Sin clasificar" (EXPENSE) y "Sueldo" (INCOME).

Ambos grupos quedaron sin ninguna subcategoría de sistema tras la
migración 0011 (simplify_system_groups) — cualquier usuario nuevo que no
creara sus propias subcategorías no podía cargar un gasto/ingreso, porque
get_user_categories()/get_expense_categories() solo devuelven subcategorías
(parent__isnull=False), nunca grupos. Reportado por un usuario real (DT-085).
"""

from django.db import migrations


def seed_default_subcategory(apps, schema_editor):
    Category = apps.get_model("categories", "Category")

    groups = {
        "EXPENSE": ("Sin clasificar", "Varios"),
        "INCOME": ("Sueldo", "Otros"),
    }

    for category_type, (group_name, subcategory_name) in groups.items():
        group = Category._default_manager.filter(
            name=group_name, type=category_type, is_system=True, user=None
        ).first()
        if not group:
            continue
        Category._default_manager.get_or_create(
            name=subcategory_name,
            type=category_type,
            is_system=True,
            user=None,
            parent=group,
            defaults={
                "icon": "bi-three-dots",
                "color": "#6c757d",
            },
        )


def reverse_seed_default_subcategory(apps, schema_editor):
    Category = apps.get_model("categories", "Category")
    Category._default_manager.filter(
        name__in=["Varios", "Otros"],
        is_system=True,
        user=None,
        parent__isnull=False,
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("categories", "0011_simplify_system_groups"),
    ]

    operations = [
        migrations.RunPython(
            seed_default_subcategory,
            reverse_seed_default_subcategory,
        ),
    ]
