"""
Comando para crear las categorías del sistema.
"""

from django.core.management.base import BaseCommand

from apps.categories.models import Category
from apps.core.constants import SYSTEM_CATEGORIES


class Command(BaseCommand):
    help = "Crea las categorías del sistema predefinidas"

    def handle(self, *args, **options):
        created_count = 0
        existing_count = 0

        for category_type, categories in SYSTEM_CATEGORIES.items():
            for cat_data in categories:
                category, created = Category.objects.get_or_create(
                    name=cat_data["name"],
                    type=category_type,
                    is_system=True,
                    defaults={
                        "icon": cat_data.get("icon", ""),
                        "color": cat_data.get("color", "#6c757d"),
                        "user": None,
                    },
                )

                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✓ Creada: {category.name} ({category_type})")
                    )
                else:
                    existing_count += 1
                    self.stdout.write(
                        self.style.WARNING(f"  - Ya existe: {category.name} ({category_type})")
                    )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(f"Resumen: {created_count} creadas, {existing_count} ya existían")
        )
