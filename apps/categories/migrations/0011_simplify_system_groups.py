"""
Migración de datos: simplificar grupos de sistema.

- Conserva: "Sin clasificar" (EXPENSE) y "Sueldo" (INCOME)
- Reasigna subcategorías de usuario de grupos eliminados a "Sin clasificar" / "Sueldo"
- Elimina el resto de grupos de sistema
"""

from django.db import migrations


def simplify_system_groups(apps, schema_editor):
    Category = apps.get_model("categories", "Category")
    Expense = apps.get_model("expenses", "Expense")
    Income = apps.get_model("income", "Income")

    to_remove = {
        "EXPENSE": [
            "Alimentación", "Educación", "Entretenimiento", "Otros gastos",
            "Ropa", "Salud", "Servicios", "Transporte", "Vivienda",
        ],
        "INCOME": ["Freelance", "Inversiones", "Otros ingresos", "Sin clasificar"],
    }

    fallback = {
        "EXPENSE": Category._default_manager.filter(
            name="Sin clasificar", type="EXPENSE", is_system=True, user=None
        ).first(),
        "INCOME": Category._default_manager.filter(
            name="Sueldo", type="INCOME", is_system=True, user=None
        ).first(),
    }

    for category_type, names in to_remove.items():
        dest = fallback[category_type]
        if not dest:
            continue
        for name in names:
            group = Category._default_manager.filter(
                name=name, type=category_type, is_system=True, user=None
            ).first()
            if not group:
                continue
            # Reasignar subcategorías de usuario al fallback
            Category._default_manager.filter(parent=group, is_system=False).update(parent=dest)
            # Reasignar transacciones que apuntan directamente al grupo
            if category_type == "EXPENSE":
                Expense._default_manager.filter(category=group).update(category=dest)
            else:
                Income._default_manager.filter(category=group).update(category=dest)
            group.delete()


def reverse_simplify_system_groups(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("categories", "0010_add_order_to_category"),
        ("expenses", "0001_initial"),
        ("income", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            simplify_system_groups,
            reverse_simplify_system_groups,
        ),
    ]
