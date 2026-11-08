from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.notifications.services import send_push_to_user


class Command(BaseCommand):
    help = "Envía un push de prueba a todos los dispositivos activos de un usuario."

    def add_arguments(self, parser):
        parser.add_argument("username")

    def handle(self, *args, **options):
        username = options["username"]
        user = get_user_model().objects.filter(username=username).first()
        if user is None:
            raise CommandError(f"No existe el usuario '{username}'.")

        sent = send_push_to_user(
            user,
            title="Control de Gastos",
            body="Notificación de prueba: las notificaciones push funcionan.",
        )
        self.stdout.write(f"Dispositivos que recibieron el push: {sent}")
