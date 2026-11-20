"""Exportación completa de los datos de un usuario a un Excel con una hoja por entidad (DT-062)."""

from django.utils import timezone

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

from apps.categories.models import Category, CategoryOverride, CategoryRule
from apps.expenses.models import Expense
from apps.income.models import Income
from apps.recurring.models import RecurringExpense
from apps.recurring_income.models import RecurringIncome
from apps.savings.models import Saving, SavingMovement
from apps.shared_expenses.models import HouseholdMember, SharedExpense

HEADER_FONT = Font(bold=True, color="FFFFFF")
HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
DATE_FORMAT = "DD/MM/YYYY"


def _yes_no(value):
    return "Sí" if value else "No"


def _group_and_name(category):
    if category is None:
        return "", ""
    if category.parent_id:
        return category.parent.name, category.name
    return category.name, ""


def _add_sheet(wb, title, headers, rows):
    ws = wb.create_sheet(title)
    ws.append(headers)
    for cell in ws[1]:
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
    for row in rows:
        ws.append(row)
    for idx, column in enumerate(ws.iter_cols(), start=1):
        longest = max(len(str(cell.value)) for cell in column if cell.value is not None)
        ws.column_dimensions[get_column_letter(idx)].width = min(50, max(12, longest + 2))
        for cell in column[1:]:
            if hasattr(cell.value, "year"):
                cell.number_format = DATE_FORMAT
    ws.freeze_panes = "A2"


def build_user_workbook(user):
    wb = Workbook()
    wb.remove(wb.active)

    profile = [
        ("Usuario", user.username),
        ("Email", user.email),
        ("Nombre", user.first_name),
        ("Apellido", user.last_name),
        ("Fecha de alta", timezone.localtime(user.date_joined).date()),
        ("Moneda por defecto", user.get_default_currency_display()),
        ("Día de inicio del mes financiero", user.financial_month_start_day),
        ("Email verificado", _yes_no(user.email_verified)),
        ("Recordatorios de gastos e ingresos fijos", _yes_no(user.recurring_reminders_enabled)),
        ("Alertas de gasto", _yes_no(user.spending_alerts_enabled)),
        ("Resúmenes", _yes_no(user.summaries_enabled)),
        ("Exportado el", timezone.localdate()),
    ]
    _add_sheet(wb, "Perfil", ["Dato", "Valor"], profile)

    hidden_ids = set(
        CategoryOverride.objects.filter(user=user, is_hidden=True).values_list(
            "category_id", flat=True
        )
    )
    categories = Category.objects.filter(user=user) | Category.objects.filter(
        is_system=True, pk__in=hidden_ids
    )
    _add_sheet(
        wb,
        "Categorías",
        ["Tipo", "Grupo", "Subcategoría", "Origen", "Oculta", "Alerta mensual"],
        [
            (
                c.get_type_display(),
                *_group_and_name(c),
                "Sistema" if c.is_system else "Propia",
                _yes_no(c.pk in hidden_ids),
                c.monthly_alert_threshold,
            )
            for c in categories.select_related("parent").order_by("type", "parent__name", "name")
        ],
    )

    _add_sheet(
        wb,
        "Reglas de categorías",
        ["Texto", "Grupo", "Subcategoría"],
        [
            (r.pattern, *_group_and_name(r.category))
            for r in CategoryRule.objects.filter(user=user)
            .select_related("category__parent")
            .order_by("pattern")
        ],
    )

    _add_sheet(
        wb,
        "Gastos",
        [
            "Fecha",
            "Grupo",
            "Subcategoría",
            "Descripción",
            "Monto",
            "Moneda",
            "Tipo de cambio",
            "Monto ARS",
            "Método de pago",
            "Meta de ahorro",
            "Gasto fijo",
        ],
        [
            (
                e.date,
                *_group_and_name(e.category),
                e.description,
                e.amount,
                e.currency,
                e.exchange_rate,
                e.amount_ars,
                e.get_payment_method_display() if e.payment_method else "",
                e.saving.name if e.saving else "",
                e.recurring.name if e.recurring else "",
            )
            for e in Expense.objects.filter(user=user)
            .select_related("category__parent", "saving", "recurring")
            .order_by("date", "pk")
        ],
    )

    _add_sheet(
        wb,
        "Ingresos",
        [
            "Fecha",
            "Grupo",
            "Subcategoría",
            "Descripción",
            "Monto",
            "Moneda",
            "Tipo de cambio",
            "Monto ARS",
            "Ingreso fijo",
        ],
        [
            (
                i.date,
                *_group_and_name(i.category),
                i.description,
                i.amount,
                i.currency,
                i.exchange_rate,
                i.amount_ars,
                i.recurring.name if i.recurring else "",
            )
            for i in Income.objects.filter(user=user)
            .select_related("category__parent", "recurring")
            .order_by("date", "pk")
        ],
    )

    _add_sheet(
        wb,
        "Gastos fijos",
        [
            "Nombre",
            "Grupo",
            "Subcategoría",
            "Día de vencimiento",
            "Monto estimado",
            "Débito automático",
            "Activo",
            "Cuotas totales",
            "Cuota inicial",
            "Fecha de inicio",
            "Notas",
        ],
        [
            (
                r.name,
                *_group_and_name(r.category),
                r.due_day,
                r.estimated_amount,
                _yes_no(r.is_auto_debit),
                _yes_no(r.is_active),
                r.total_installments,
                r.starting_installment,
                r.start_date,
                r.notes,
            )
            for r in RecurringExpense.objects.filter(user=user)
            .select_related("category__parent")
            .order_by("name")
        ],
    )

    _add_sheet(
        wb,
        "Ingresos fijos",
        ["Nombre", "Grupo", "Subcategoría", "Día esperado", "Activo", "Notas"],
        [
            (r.name, *_group_and_name(r.category), r.expected_day, _yes_no(r.is_active), r.notes)
            for r in RecurringIncome.objects.filter(user=user)
            .select_related("category__parent")
            .order_by("name")
        ],
    )

    _add_sheet(
        wb,
        "Metas de ahorro",
        [
            "Nombre",
            "Descripción",
            "Objetivo",
            "Acumulado",
            "Moneda",
            "Fecha objetivo",
            "Estado",
        ],
        [
            (
                s.name,
                s.description,
                s.target_amount,
                s.current_amount,
                s.currency,
                s.target_date,
                s.get_status_display(),
            )
            for s in Saving.objects.filter(user=user).order_by("name")
        ],
    )

    _add_sheet(
        wb,
        "Movimientos de ahorro",
        ["Fecha", "Meta", "Tipo", "Monto", "Descripción"],
        [
            (m.date, m.saving.name, m.get_type_display(), m.amount, m.description)
            for m in SavingMovement.objects.filter(saving__user=user)
            .select_related("saving")
            .order_by("date", "pk")
        ],
    )

    _add_sheet(
        wb,
        "Integrantes del hogar",
        ["Nombre"],
        [(m.name,) for m in HouseholdMember.objects.filter(user=user).order_by("name")],
    )

    _add_sheet(
        wb,
        "Gastos compartidos",
        [
            "Fecha",
            "Grupo",
            "Subcategoría",
            "Descripción",
            "Monto",
            "Moneda",
            "Tipo de cambio",
            "Monto ARS",
            "Pagó",
        ],
        [
            (
                s.date,
                *_group_and_name(s.category),
                s.description,
                s.amount,
                s.currency,
                s.exchange_rate,
                s.amount_ars,
                s.paid_by.name if s.paid_by else "",
            )
            for s in SharedExpense.objects.filter(user=user)
            .select_related("category__parent", "paid_by")
            .order_by("date", "pk")
        ],
    )

    return wb
