from datetime import date

from django.core.management.base import BaseCommand, CommandError

from apps.notifications.reminders import send_recurring_reminders


class Command(BaseCommand):
    help = "Envía el recordatorio push de gastos fijos que vencen en 3 días (pensado para un cron diario)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--date",
            help="Fecha a usar como 'hoy' (AAAA-MM-DD), para pruebas. Por defecto, hoy en hora local.",
        )

    def handle(self, *args, **options):
        today = None
        if options["date"]:
            try:
                today = date.fromisoformat(options["date"])
            except ValueError as exc:
                raise CommandError("--date debe tener formato AAAA-MM-DD.") from exc

        notified = send_recurring_reminders(today)
        self.stdout.write(f"Usuarios notificados: {notified}")
