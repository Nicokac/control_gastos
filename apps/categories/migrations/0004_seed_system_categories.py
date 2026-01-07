from django.db import migrations


def seed_system_categories(apps, schema_editor):
    Category = apps.get_model("categories", "Category")

    SYSTEM_CATEGORIES = {
        "EXPENSE": [
            {"name": "Alimentación", "icon": "bi-cart", "color": "#28a745"},
            {"name": "Transporte", "icon": "bi-car-front", "color": "#17a2b8"},
            {"name": "Vivienda", "icon": "bi-house", "color": "#6c757d"},
            {"name": "Servicios", "icon": "bi-lightning", "color": "#ffc107"},
            {"name": "Salud", "icon": "bi-heart-pulse", "color": "#dc3545"},
            {"name": "Entretenimiento", "icon": "bi-controller", "color": "#e83e8c"},
            {"name": "Educación", "icon": "bi-book", "color": "#6f42c1"},
            {"name": "Ropa", "icon": "bi-bag", "color": "#fd7e14"},
            {"name": "Otros gastos", "icon": "bi-three-dots", "color": "#6c757d"},
        ],
        "INCOME": [
            {"name": "Sueldo", "icon": "bi-briefcase", "color": "#28a745"},
            {"name": "Freelance", "icon": "bi-laptop", "color": "#17a2b8"},
            {"name": "Inversiones", "icon": "bi-graph-up-arrow", "color": "#6f42c1"},
            {"name": "Otros ingresos", "icon": "bi-three-dots", "color": "#6c757d"},
        ],
    }

    manager = Category._default_manager  # <-- clave

    for category_type, categories in SYSTEM_CATEGORIES.items():
        for cat_data in categories:
            manager.get_or_create(
                name=cat_data["name"],
                type=category_type,
                is_system=True,
                user=None,
                defaults={
                    "icon": cat_data.get("icon", ""),
                    "color": cat_data.get("color", "#6c757d"),
                },
            )


def unseed_system_categories(apps, schema_editor):
    Category = apps.get_model("categories", "Category")
    Category._default_manager.filter(is_system=True, user=None).delete()  # <-- clave


class Migration(migrations.Migration):
    dependencies = [
        ("categories", "0003_category_categories__user_id_135dec_idx_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_system_categories, unseed_system_categories),
    ]
