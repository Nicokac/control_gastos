from datetime import date

from django.core.management.base import BaseCommand, CommandError

from apps.notifications.reminders import send_recurring_reminders


class Command(BaseCommand):
    help = "Envía los avisos push de gastos fijos por vencer (en 3 días) y vencidos ayer sin pagar (cron diario)."

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
        self.stdout.write(f"Avisos enviados: {notified}")
