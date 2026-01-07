import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crea/actualiza un superusuario desde variables de entorno (para deploys sin shell)."

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

        if not username or not password:
            self.stdout.write(
                self.style.WARNING(
                    "DJANGO_SUPERUSER_USERNAME/PASSWORD no están seteadas. No se crea superusuario."
                )
            )
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "is_staff": True, "is_superuser": True},
        )

        # Si ya existía, garantizamos flags
        if not user.is_staff or not user.is_superuser:
            user.is_staff = True
            user.is_superuser = True
            if email:
                user.email = email

        # Siempre seteamos password (para que puedas rotarla desde ENV)
        user.set_password(password)
        user.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f"✓ Superusuario creado: {username}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"✓ Superusuario actualizado: {username}"))
