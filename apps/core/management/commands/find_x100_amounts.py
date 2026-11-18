"""
Lista registros que probablemente quedaron con el monto multiplicado por 100
por el bug de edición de la app mobile (corregido en Mobile 1.29.0+39).
Solo lectura. Uso: python manage.py find_x100_amounts [--min-ratio 20] [--user email]
"""

from collections import defaultdict
from datetime import timedelta
from decimal import Decimal
from statistics import median

from django.core.management.base import BaseCommand

from apps.expenses.models import Expense
from apps.income.models import Income
from apps.savings.models import Saving
from apps.shared_expenses.models import SharedExpense

EDIT_GAP = timedelta(minutes=1)

# (etiqueta, modelo, campo que se muestra, campo que se compara, campo de agrupación, campo de texto)
SOURCES = [
    ("Gasto", Expense, "amount", "amount_ars", "category_id", "description"),
    ("Ingreso", Income, "amount", "amount_ars", "category_id", "description"),
    ("Gasto compartido", SharedExpense, "amount", "amount_ars", "category_id", "description"),
    ("Meta de ahorro", Saving, "target_amount", "target_amount", "currency", "name"),
]


class Command(BaseCommand):
    help = (
        "Lista montos sospechosos de haber quedado x100 por el bug de edición mobile (solo lectura)"
    )

    def add_arguments(self, parser):
        parser.add_argument("--min-ratio", type=Decimal, default=Decimal("20"))
        parser.add_argument("--user", type=str, help="Email del usuario a revisar")

    def handle(self, *args, **options):
        min_ratio = options["min_ratio"]
        total = 0
        without_reference = []

        for label, model, shown, compared, group, text in SOURCES:
            qs = model.objects.select_related("user")
            if options["user"]:
                qs = qs.filter(user__email__iexact=options["user"])
            rows = list(qs)

            groups = defaultdict(list)
            for row in rows:
                groups[(row.user_id, getattr(row, group))].append(row)

            for row in rows:
                amount = getattr(row, shown)
                if (
                    row.updated_at - row.created_at < EDIT_GAP
                    or amount != amount.to_integral_value()
                ):
                    continue
                others = [
                    getattr(o, compared)
                    for o in groups[(row.user_id, getattr(row, group))]
                    if o.pk != row.pk
                ]
                if not others:
                    without_reference.append((label, row, amount, text))
                    continue
                reference = median(others)
                ratio = getattr(row, compared) / reference
                if ratio < min_ratio:
                    continue
                total += 1
                self.stdout.write(
                    f"{label} #{row.pk} | {row.user.email} | editado {row.updated_at:%Y-%m-%d} | "
                    f"{getattr(row, text)!r} | monto {amount} -> {amount / 100} | "
                    f"{ratio:.0f}x la mediana ({reference})"
                )

        self.stdout.write(f"\nSospechosos: {total} (umbral {min_ratio}x la mediana)")

        if without_reference:
            self.stdout.write(
                f"\nEditados sin otros registros para comparar ({len(without_reference)}), revisar a mano:"
            )
            for label, row, amount, text in without_reference:
                self.stdout.write(
                    f"{label} #{row.pk} | {row.user.email} | editado {row.updated_at:%Y-%m-%d} | "
                    f"{getattr(row, text)!r} | monto {amount}"
                )
