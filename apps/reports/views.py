"""
Vistas para dashboard y reportes.
"""

from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Sum
from django.utils import timezone
from django.views.generic import TemplateView

from apps.budgets.models import Budget
from apps.core.utils import get_month_date_range_exclusive, get_month_name
from apps.expenses.models import Expense
from apps.income.models import Income
from apps.savings.models import Saving, SavingStatus


class DashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard principal con resumen financiero."""

    template_name = "reports/dashboard.html"

    def get_context_data(self, **kwargs):
        """Construye el contexto con todos los datos del dashboard."""
        context = super().get_context_data(**kwargs)

        user = self.request.user
        today = timezone.now().date()
        current_month = today.month
        current_year = today.year

        # Información del período
        context["current_month"] = current_month
        context["current_year"] = current_year
        context["month_name"] = get_month_name(current_month)
        context["today"] = today

        # Obtener datos de cada módulo
        context.update(self._get_balance_data(user, current_month, current_year))
        context.update(self._get_budget_data(user, current_month, current_year))
        context.update(self._get_savings_data(user))
        context.update(self._get_recent_transactions(user))
        context.update(self._get_expense_distribution(user, current_month, current_year))

        return context

    def _get_balance_data(self, user, month, year):
        """
        Obtiene datos de balance: ingresos vs gastos.

        Optimizado: 2 queries en lugar de 6.
        """

        # Rango mes actual
        cur_start, cur_end = get_month_date_range_exclusive(month, year)

        # Calcular mes anterior
        if month == 1:
            prev_month, prev_year = 12, year - 1
        else:
            prev_month, prev_year = month - 1, year

        prev_start, prev_end = get_month_date_range_exclusive(prev_month, prev_year)

        # Query 1: Gastos (mes actual + anterior)
        expense_data = (
            Expense.objects.filter(user=user)
            .filter(
                Q(date__gte=cur_start, date__lt=cur_end)
                | Q(date__gte=prev_start, date__lt=prev_end)
            )
            .aggregate(
                current=Sum("amount_ars", filter=Q(date__gte=cur_start, date__lt=cur_end)),
                previous=Sum("amount_ars", filter=Q(date__gte=prev_start, date__lt=prev_end)),
            )
        )

        # Query 2: Ingresos (mes actual + anterior)
        income_data = (
            Income.objects.filter(user=user)
            .filter(
                Q(date__gte=cur_start, date__lt=cur_end)
                | Q(date__gte=prev_start, date__lt=prev_end)
            )
            .aggregate(
                current=Sum("amount_ars", filter=Q(date__gte=cur_start, date__lt=cur_end)),
                previous=Sum("amount_ars", filter=Q(date__gte=prev_start, date__lt=prev_end)),
            )
        )

        # Extraer valores
        expense_total = expense_data["current"] or Decimal("0")
        prev_expense_total = expense_data["previous"] or Decimal("0")
        income_total = income_data["current"] or Decimal("0")
        prev_income_total = income_data["previous"] or Decimal("0")

        # Balance
        balance = income_total - expense_total

        # Porcentaje de gastos vs ingresos
        if income_total > 0:
            expense_percentage = round((expense_total / income_total) * 100, 1)
        else:
            expense_percentage = 0

        # Variación porcentual de gastos
        if prev_expense_total > 0:
            expense_variation = round(
                ((expense_total - prev_expense_total) / prev_expense_total) * 100, 1
            )
        else:
            expense_variation = 0

        # Variación porcentual de ingresos
        if prev_income_total > 0:
            income_variation = round(
                ((income_total - prev_income_total) / prev_income_total) * 100, 1
            )
        else:
            income_variation = 0

        return {
            "income_total": income_total,
            "expense_total": expense_total,
            "balance": balance,
            "balance_is_positive": balance >= 0,
            "expense_percentage": expense_percentage,
            "expense_variation": expense_variation,
            "income_variation": income_variation,
            "prev_month_name": get_month_name(prev_month),
        }

    def _get_budget_data(self, user, month, year):
        """Obtiene datos de presupuestos del mes."""
        budgets = Budget.get_with_spent(user, month=month, year=year)

        # Contadores
        budget_list = list(budgets)
        total_budgets = len(budget_list)
        over_budget = sum(1 for b in budget_list if b.is_over_budget)
        near_limit = sum(1 for b in budget_list if b.is_near_limit)
        on_track = total_budgets - over_budget - near_limit

        # Totales
        total_budgeted = sum(b.amount for b in budget_list)
        total_spent = sum(b.spent_amount for b in budget_list)

        if total_budgeted > 0:
            overall_percentage = round((total_spent / total_budgeted) * 100, 1)
        else:
            overall_percentage = 0

        # Top 3 presupuestos más gastados (que no estén en 0)
        top_budgets = sorted(
            [b for b in budget_list if b.spent_amount > 0],
            key=lambda x: x.spent_percentage,
            reverse=True,
        )[:3]

        return {
            "budgets": budget_list,
            "budget_count": total_budgets,
            "budgets_over": over_budget,
            "budgets_warning": near_limit,
            "budgets_ok": on_track,
            "budget_total": total_budgeted,
            "budget_spent": total_spent,
            "budget_percentage": overall_percentage,
            "top_budgets": top_budgets,
        }

    def _get_savings_data(self, user):
        """Obtiene datos de metas de ahorro activas."""
        active_savings = list(Saving.objects.filter(user=user, status=SavingStatus.ACTIVE))

        # Totales
        total_target = sum(s.target_amount for s in active_savings)
        total_current = sum(s.current_amount for s in active_savings)

        if total_target > 0:
            overall_progress = round((total_current / total_target) * 100, 1)
        else:
            overall_progress = 0

        # Metas completadas este mes
        today = timezone.now().date()
        month_start, month_end = get_month_date_range_exclusive(today.month, today.year)
        completed_this_month = Saving.objects.filter(
            user=user,
            status=SavingStatus.COMPLETED,
            updated_at__gte=month_start,
            updated_at__lt=month_end,
        ).count()

        # Top 3 metas por progreso
        top_savings = sorted(active_savings, key=lambda x: x.progress_percentage, reverse=True)[:3]

        return {
            "savings_count": len(active_savings),
            "savings_total_target": total_target,
            "savings_total_current": total_current,
            "savings_progress": overall_progress,
            "savings_completed_month": completed_this_month,
            "top_savings": top_savings,
        }

    def _get_recent_transactions(self, user):
        """
        Obtiene las últimas 8 transacciones (gastos e ingresos combinados).

        Optimizado: Usa queries separadas pero obtiene suficientes registros
        para garantizar las 8 transacciones más recientes reales.
        """
        # Obtener últimos 8 de cada tipo para garantizar cobertura
        recent_expenses = list(
            Expense.objects.filter(user=user)
            .select_related("category")
            .order_by("-date", "-created_at")[:8]
        )

        recent_incomes = list(
            Income.objects.filter(user=user)
            .select_related("category")
            .order_by("-date", "-created_at")[:8]
        )

        # Combinar en lista unificada
        transactions = []

        for expense in recent_expenses:
            transactions.append(
                {
                    "type": "expense",
                    "date": expense.date,
                    "created_at": expense.created_at,
                    "description": expense.description,
                    "amount": expense.amount_ars,
                    "formatted_amount": expense.formatted_amount,
                    "category": expense.category,
                    "pk": expense.pk,
                }
            )

        for income in recent_incomes:
            transactions.append(
                {
                    "type": "income",
                    "date": income.date,
                    "created_at": income.created_at,
                    "description": income.description,
                    "amount": income.amount_ars,
                    "formatted_amount": income.formatted_amount,
                    "category": income.category,
                    "pk": income.pk,
                }
            )

        # Ordenar por fecha y created_at descendente, luego cortar a 8
        transactions.sort(key=lambda x: (x["date"], x["created_at"]), reverse=True)

        return {
            "recent_transactions": transactions[:8],
        }

    def _get_expense_distribution(self, user, month, year):
        """Obtiene distribución de gastos por categoría para el gráfico."""
        start_date, end_date = get_month_date_range_exclusive(month, year)
        distribution = (
            Expense.objects.filter(user=user, date__gte=start_date, date__lt=end_date)
            .values("category__name", "category__color", "category__icon")
            .annotate(total=Sum("amount_ars"))
            .order_by("-total")[:6]
        )

        # Preparar datos para el gráfico
        chart_labels = []
        chart_data = []
        chart_colors = []

        for item in distribution:
            chart_labels.append(item["category__name"])
            chart_data.append(float(item["total"]))
            chart_colors.append(item["category__color"] or "#6c757d")

        return {
            "expense_distribution": list(distribution),
            "chart_labels": chart_labels,
            "chart_data": chart_data,
            "chart_colors": chart_colors,
        }
