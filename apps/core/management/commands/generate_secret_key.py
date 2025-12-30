"""
Comando para generar una SECRET_KEY segura.
Uso: python manage.py generate_secret_key
"""

from django.core.management.base import BaseCommand
from django.core.management.utils import get_random_secret_key


class Command(BaseCommand):
    help = "Genera una SECRET_KEY segura para usar en producción"

    def add_arguments(self, parser):
        parser.add_argument(
            "--length",
            type=int,
            default=50,
            help="Longitud mínima de la clave (default: 50)",
        )
        parser.add_argument(
            "--env-format",
            action="store_true",
            help="Mostrar en formato para archivo .env",
        )
        parser.add_argument(
            "--export-format",
            action="store_true",
            help="Mostrar en formato para export de shell",
        )

    def handle(self, *args, **options):
        # Generar clave
        secret_key = get_random_secret_key()

        # Asegurar longitud mínima
        while len(secret_key) < options["length"]:
            secret_key += get_random_secret_key()

        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("🔐 SECRET_KEY generada exitosamente"))
        self.stdout.write("=" * 60)
        self.stdout.write("")

        if options["env_format"]:
            self.stdout.write("Formato .env:")
            self.stdout.write(f"SECRET_KEY={secret_key}")
        elif options["export_format"]:
            self.stdout.write("Formato export (Linux/Mac):")
            self.stdout.write(f"export SECRET_KEY='{secret_key}'")
            self.stdout.write("")
            self.stdout.write("Formato set (Windows CMD):")
            self.stdout.write(f"set SECRET_KEY={secret_key}")
            self.stdout.write("")
            self.stdout.write("Formato PowerShell:")
            self.stdout.write(f"$env:SECRET_KEY='{secret_key}'")
        else:
            self.stdout.write("SECRET_KEY:")
            self.stdout.write(self.style.WARNING(secret_key))

        self.stdout.write("")
        self.stdout.write(f"Longitud: {len(secret_key)} caracteres")
        self.stdout.write("=" * 60)
        self.stdout.write("")

        self.stdout.write(
            self.style.NOTICE(
                "⚠️  IMPORTANTE: Guarda esta clave de forma segura.\n"
                "   No la compartas ni la subas a control de versiones."
            )
        )
