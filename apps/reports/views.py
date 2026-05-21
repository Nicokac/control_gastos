"""
Vistas para dashboard y reportes.
"""

from datetime import datetime, time
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Sum
from django.utils import timezone
from django.views.generic import TemplateView

from apps.core.utils import get_month_date_range_exclusive, get_month_name
from apps.expenses.models import Expense
from apps.income.models import Income
from apps.savings.models import MovementType, Saving, SavingMovement, SavingStatus


class DashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard principal con resumen financiero."""

    template_name = "reports/dashboard.html"

    def get_context_data(self, **kwargs):
        """Construye el contexto con todos los datos del dashboard."""
        context = super().get_context_data(**kwargs)

        user = self.request.user
        today = timezone.localdate()
        current_month = today.month
        current_year = today.year

        # Año seleccionado para el gráfico de evolución (por defecto: año actual)
        try:
            selected_year = int(self.request.GET.get("year", current_year))
        except (ValueError, TypeError):
            selected_year = current_year
        # Limitar a años con datos posibles (2020 → año actual)
        selected_year = max(2020, min(selected_year, current_year))

        # Para el gráfico: si es el año actual mostrar hasta el mes actual;
        # si es un año anterior mostrar los 12 meses completos
        evolution_month = current_month if selected_year == current_year else 12

        # Años disponibles para el selector (desde el primer año con datos hasta hoy)
        first_year = self._get_first_data_year(user, current_year)
        year_choices = list(range(first_year, current_year + 1))

        # Información del período
        context["current_month"] = current_month
        context["current_year"] = current_year
        context["month_name"] = get_month_name(current_month)
        context["today"] = today
        context["selected_year"] = selected_year
        context["year_choices"] = year_choices

        # Obtener datos de cada módulo
        context.update(self._get_balance_data(user, current_month, current_year))
        context.update(self._get_savings_data(user))
        context.update(self._get_recurring_data(user, current_month, current_year))
        context.update(self._get_recent_transactions(user))
        context.update(self._get_expense_distribution(user, current_month, current_year))
        context.update(self._get_monthly_evolution(user, evolution_month, selected_year))

        return context

    def _get_first_data_year(self, user, current_year):
        """Retorna el año más antiguo con datos del usuario (mínimo 2020)."""
        expense_year = (
            Expense.objects.filter(user=user)
            .order_by("date")
            .values_list("date__year", flat=True)
            .first()
        )
        income_year = (
            Income.objects.filter(user=user)
            .order_by("date")
            .values_list("date__year", flat=True)
            .first()
        )
        candidates = [y for y in [expense_year, income_year] if y]
        return min(candidates) if candidates else current_year

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

        # Query 3: Depósitos a ahorro del mes actual
        savings_deposits_data = SavingMovement.objects.filter(
            saving__user=user,
            type=MovementType.DEPOSIT,
            date__gte=cur_start,
            date__lt=cur_end,
        ).aggregate(total=Sum("amount"))
        savings_deposits_total = savings_deposits_data["total"] or Decimal("0")

        # Balance (ingresos - gastos - ahorro)
        balance = income_total - expense_total - savings_deposits_total

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
            "savings_deposits_total": savings_deposits_total,
            "balance": balance,
            "balance_is_positive": balance >= 0,
            "expense_percentage": expense_percentage,
            "expense_variation": expense_variation,
            "income_variation": income_variation,
            "prev_income_total": prev_income_total,
            "prev_month_name": get_month_name(prev_month),
        }

    def _get_savings_data(self, user):
        """Obtiene datos de metas de ahorro activas."""
        today = timezone.localdate()
        month_start_date, month_end_date = get_month_date_range_exclusive(today.month, today.year)

        # Convertir a datetime aware para filtrar DateTimeField (updated_at)
        month_start = timezone.make_aware(datetime.combine(month_start_date, time.min))
        month_end = timezone.make_aware(datetime.combine(month_end_date, time.min))

        # Query 1: Aggregates (totales + count completed) en una sola query
        aggregates = Saving.objects.filter(user=user).aggregate(
            total_target=Sum(
                "target_amount", filter=Q(status=SavingStatus.ACTIVE), default=Decimal("0")
            ),
            total_current=Sum(
                "current_amount", filter=Q(status=SavingStatus.ACTIVE), default=Decimal("0")
            ),
            active_count=Count("pk", filter=Q(status=SavingStatus.ACTIVE)),
            completed_this_month=Count(
                "pk",
                filter=Q(
                    status=SavingStatus.COMPLETED,
                    updated_at__gte=month_start,
                    updated_at__lt=month_end,
                ),
            ),
        )

        total_target = aggregates["total_target"]
        total_current = aggregates["total_current"]

        if total_target > 0:
            overall_progress = round((total_current / total_target) * 100, 1)
        else:
            overall_progress = 0

        from django.db.models import DecimalField, ExpressionWrapper, F

        # Query 2: Top 3 metas activas por progreso (ordenado en DB)
        progress_expr = ExpressionWrapper(
            (F("current_amount") * 100) / F("target_amount"),
            output_field=DecimalField(max_digits=7, decimal_places=2),
        )

        top_savings = list(
            Saving.objects.filter(user=user, status=SavingStatus.ACTIVE)
            .annotate(progress_db=progress_expr)
            .order_by("-progress_db", "-updated_at")[:3]
        )

        return {
            "savings_count": aggregates["active_count"],
            "savings_total_target": total_target,
            "savings_total_current": total_current,
            "savings_progress": overall_progress,
            "savings_completed_month": aggregates["completed_this_month"],
            "top_savings": top_savings,
        }

    def _get_recurring_data(self, user, month, year):
        """Obtiene el estado de gastos fijos del mes actual."""
        from apps.recurring.models import RecurringExpense

        recurrents = RecurringExpense.objects.filter(user=user, is_active=True).prefetch_related(
            "expenses"
        )
        total_active = len(recurrents)
        total_paid = sum(1 for r in recurrents if r.is_paid_in(month, year))
        overdue = sum(
            1
            for r in recurrents
            if not r.is_paid_in(month, year) and r.status_for(month, year) == "overdue"
        )
        pending = [
            {"rec": r, "overdue": r.status_for(month, year) == "overdue"}
            for r in recurrents
            if not r.is_paid_in(month, year)
        ]

        return {
            "recurring_total": total_active,
            "recurring_paid": total_paid,
            "recurring_overdue": overdue,
            "recurring_pending": pending,
        }

    def _get_recent_transactions(self, user):
        """
        Obtiene las últimas 5 transacciones (gastos e ingresos combinados).

        Optimizado: Usa queries separadas pero obtiene suficientes registros
        para garantizar las 5 transacciones más recientes reales.
        """
        # Obtener últimos 5 de cada tipo para garantizar cobertura
        recent_expenses = list(
            Expense.objects.filter(user=user)
            .select_related("category")
            .order_by("-date", "-created_at")[:5]
        )

        recent_incomes = list(
            Income.objects.filter(user=user)
            .select_related("category")
            .order_by("-date", "-created_at")[:5]
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

        # Ordenar por fecha y created_at descendente, luego cortar a 5
        transactions.sort(key=lambda x: (x["date"], x["created_at"]), reverse=True)

        return {
            "recent_transactions": transactions[:5],
        }

    def _get_monthly_evolution(self, user, month, year):
        """
        Retorna ingresos, gastos y ahorro acumulados por mes,
        desde enero del año actual hasta el mes actual inclusive.
        """
        months = range(1, month + 1)
        labels = []
        income_data = []
        expense_data = []
        savings_data = []
        balance_data = []

        # Rango completo: enero → fin del mes actual (1 query por modelo)
        year_start, _ = get_month_date_range_exclusive(1, year)
        _, period_end = get_month_date_range_exclusive(month, year)

        expenses_qs = (
            Expense.objects.filter(user=user, date__gte=year_start, date__lt=period_end)
            .values("date__month")
            .annotate(total=Sum("amount_ars"))
        )
        incomes_qs = (
            Income.objects.filter(user=user, date__gte=year_start, date__lt=period_end)
            .values("date__month")
            .annotate(total=Sum("amount_ars"))
        )
        savings_qs = (
            SavingMovement.objects.filter(
                saving__user=user,
                type=MovementType.DEPOSIT,
                date__gte=year_start,
                date__lt=period_end,
            )
            .values("date__month")
            .annotate(total=Sum("amount"))
        )

        expense_by_month = {row["date__month"]: float(row["total"]) for row in expenses_qs}
        income_by_month = {row["date__month"]: float(row["total"]) for row in incomes_qs}
        savings_by_month = {row["date__month"]: float(row["total"]) for row in savings_qs}

        for m in months:
            inc = income_by_month.get(m, 0)
            exp = expense_by_month.get(m, 0)
            sav = savings_by_month.get(m, 0)
            labels.append(get_month_name(m))
            income_data.append(inc)
            expense_data.append(exp)
            savings_data.append(sav)
            balance_data.append(round(inc - exp - sav, 2))

        return {
            "evolution_labels": labels,
            "evolution_income": income_data,
            "evolution_expenses": expense_data,
            "evolution_savings": savings_data,
            "evolution_balance": balance_data,
        }

    def _get_expense_distribution(self, user, month, year):
        """
        Obtiene distribución de gastos agrupada por grupo padre de la categoría.

        Retorna:
        - ranking_distribution: grupos ordenados por total (para el ranking con scroll)
        - chart_*: top 5 grupos + "Otros" agrupado (para el donut)
        """
        start_date, end_date = get_month_date_range_exclusive(month, year)

        raw = list(
            Expense.objects.filter(user=user, date__gte=start_date, date__lt=end_date)
            .select_related("category__parent")
            .values(
                "category__parent__id",
                "category__parent__name",
                "category__parent__color",
                "category__id",
                "category__name",
                "category__color",
                "category__icon",
            )
            .annotate(total=Sum("amount_ars"))
            .order_by("-total")
        )

        # Agrupar por grupo padre; si no tiene padre usar la categoría misma como grupo
        groups: dict = {}
        for item in raw:
            group_name = (
                item["category__parent__name"] or item["category__name"] or "Sin clasificar"
            )
            group_color = item["category__parent__color"] or item["category__color"] or "#6c757d"
            group_pk = item["category__parent__id"] or item["category__id"]
            if group_name not in groups:
                groups[group_name] = {
                    "name": group_name,
                    "color": group_color,
                    "pk": group_pk,
                    "total": Decimal("0"),
                    "subcategories": [],
                }
            groups[group_name]["total"] += item["total"]
            # Solo agregar subcategoría si la categoría tiene padre (no es el grupo mismo)
            if item["category__parent__name"]:
                groups[group_name]["subcategories"].append(
                    {
                        "name": item["category__name"],
                        "pk": item["category__id"],
                        "icon": item["category__icon"] or "",
                        "total": item["total"],
                    }
                )

        grand_total = sum(float(g["total"]) for g in groups.values())

        ranking = sorted(groups.values(), key=lambda g: g["total"], reverse=True)
        for item in ranking:
            item["percentage"] = (
                round((float(item["total"]) / grand_total) * 100, 1) if grand_total > 0 else 0
            )

        # Donut: top 5 grupos + "Otros"
        TOP_N = 5
        top = ranking[:TOP_N]
        others = ranking[TOP_N:]

        chart_labels = [r["name"] for r in top]
        chart_data = [float(r["total"]) for r in top]
        chart_colors = [r["color"] for r in top]

        if others:
            others_total = sum(float(r["total"]) for r in others)
            chart_labels.append("Otros")
            chart_data.append(others_total)
            chart_colors.append("#6c757d")

        top_category = ranking[0] if ranking else None

        return {
            "ranking_distribution": ranking,
            "chart_labels": chart_labels,
            "chart_data": chart_data,
            "chart_colors": chart_colors,
            "chart_grand_total": grand_total,
            "top_category": top_category,
            "expense_distribution": ranking,
        }
