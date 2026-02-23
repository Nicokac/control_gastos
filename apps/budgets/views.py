"""
Vistas para gestión de presupuestos.
"""

import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import FormView

from apps.core.views import (
    UserOwnedCreateView,
    UserOwnedDeleteView,
    UserOwnedDetailView,
    UserOwnedListView,
    UserOwnedUpdateView,
)

from .forms import BudgetFilterForm, BudgetForm, CopyBudgetsForm
from .models import Budget

logger = logging.getLogger("apps.budgets")


class BudgetListView(UserOwnedListView):
    """Lista de presupuestos del usuario con filtros."""

    model = Budget
    template_name = "budgets/budget_list.html"
    context_object_name = "budgets"
    paginate_by = 12  # Override del default 20

    def get_queryset(self):
        """Filtra presupuestos del usuario actual con spent pre-calculado."""
        # Determinar período
        month = self.request.GET.get("month")
        year = self.request.GET.get("year")
        category = self.request.GET.get("category")

        # Valores por defecto: mes actual
        if not month and not year:
            from django.utils import timezone

            today = timezone.now().date()
            month = today.month
            year = today.year

        # Validar parámetros
        try:
            if month:
                month = int(month)
                if not (1 <= month <= 12):
                    month = None
            if year:
                year = int(year)
                if not (2020 <= year <= 2100):
                    year = None
        except (ValueError, TypeError) as e:
            logger.debug(f"BudgetListView: filtro inválido ignorado - {e}")
            month = None
            year = None

        # Usar método optimizado que evita N+1
        queryset = Budget.get_with_spent(user=self.request.user, month=month, year=year)

        # Filtro adicional por categoría
        if category:
            try:
                category_id = int(category)
                queryset = queryset.filter(category_id=category_id)
            except (ValueError, TypeError) as e:
                logger.debug(f"BudgetListView: filtro categoría inválido - {e}")

        return queryset

    def get_context_data(self, **kwargs):
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)

        # Formulario de filtros
        context["filter_form"] = BudgetFilterForm(
            data=self.request.GET or None, user=self.request.user
        )

        # Determinar período actual
        month = self.request.GET.get("month")
        year = self.request.GET.get("year")

        if not month or not year:
            from django.utils import timezone

            today = timezone.now().date()
            month = today.month
            year = today.year
        else:
            try:
                month = int(month)
                year = int(year)
            except (ValueError, TypeError):
                from django.utils import timezone

                today = timezone.now().date()
                month = today.month
                year = today.year

        context["current_month"] = month
        context["current_year"] = year

        # Calcular resumen usando los presupuestos ya cargados (con _spent_annotated)
        budgets = list(context["budgets"])

        total_budgeted = sum(b.amount for b in budgets)
        total_spent = sum(b.spent_amount for b in budgets)

        context["summary"] = {
            "total_budgeted": total_budgeted,
            "total_spent": total_spent,
            "total_remaining": total_budgeted - total_spent,
            "overall_percentage": round((total_spent / total_budgeted * 100), 1)
            if total_budgeted > 0
            else 0,
            "budget_count": len(budgets),
            "over_budget_count": sum(1 for b in budgets if b.is_over_budget),
            "warning_count": sum(1 for b in budgets if b.is_near_limit),
        }

        # Nombre del mes
        from apps.core.utils import get_month_name

        context["period_name"] = f"{get_month_name(month)} {year}"

        return context


class BudgetCreateView(UserOwnedCreateView):
    """Crear nuevo presupuesto."""

    model = Budget
    form_class = BudgetForm
    template_name = "budgets/budget_form.html"
    success_url = reverse_lazy("budgets:list")

    def get_success_message(self):
        return f"Presupuesto para {self.object.category.name} creado correctamente."

    def form_invalid(self, form):
        """Muestra errores."""
        messages.error(self.request, "Corregí los errores del formulario.")
        return super().form_invalid(form)


class BudgetUpdateView(UserOwnedUpdateView):
    """Editar presupuesto existente."""

    model = Budget
    form_class = BudgetForm
    template_name = "budgets/budget_form.html"
    success_url = reverse_lazy("budgets:list")

    def get_success_message(self):
        return f"Presupuesto para {self.object.category.name} actualizado correctamente."


class BudgetDeleteView(UserOwnedDeleteView):
    """Eliminar presupuesto."""

    model = Budget
    template_name = "budgets/budget_confirm_delete.html"
    success_url = reverse_lazy("budgets:list")

    def get_success_message(self, obj):
        return f"Presupuesto para '{obj.category.name}' eliminado correctamente."


class BudgetDetailView(UserOwnedDetailView):
    """Ver detalle de un presupuesto."""

    model = Budget
    template_name = "budgets/budget_detail.html"
    context_object_name = "budget"

    def get_queryset(self):
        """Usa método optimizado con spent pre-calculado."""
        return Budget.get_with_spent(user=self.request.user)

    def get_context_data(self, **kwargs):
        """Agrega gastos del período y comparación año anterior."""
        context = super().get_context_data(**kwargs)

        budget = self.object

        # Obtener gastos de esta categoría en el período
        from apps.expenses.models import Expense

        context["expenses"] = Expense.objects.filter(
            user=self.request.user,
            category=budget.category,
            date__month=budget.month,
            date__year=budget.year,
        ).order_by("-date")[:10]

        # Comparación con año anterior
        try:
            last_year_budget = Budget.objects.get(
                user=self.request.user,
                category=budget.category,
                month=budget.month,
                year=budget.year - 1,
            )
            context["last_year_budget"] = last_year_budget

            # Calcular diferencia
            current_spent = budget.spent_amount
            last_year_spent = last_year_budget.spent_amount
            difference = current_spent - last_year_spent

            context["year_comparison"] = {
                "last_year_spent": last_year_spent,
                "current_spent": current_spent,
                "difference": difference,
                "difference_abs": abs(difference),
                "is_increase": difference > 0,
                "is_decrease": difference < 0,
                "percentage_change": round((difference / last_year_spent * 100), 1)
                if last_year_spent > 0
                else 0,
            }
        except Budget.DoesNotExist:
            context["last_year_budget"] = None
            context["year_comparison"] = None

        return context


class CopyBudgetsView(LoginRequiredMixin, FormView):
    """Copiar presupuestos del mes anterior."""

    form_class = CopyBudgetsForm
    template_name = "budgets/budget_copy.html"
    success_url = reverse_lazy("budgets:list")

    def form_valid(self, form):
        """Copia los presupuestos con feedback detallado."""
        from apps.core.utils import get_month_name

        target_month = int(form.cleaned_data["target_month"])
        target_year = int(form.cleaned_data["target_year"])

        # Calcular mes origen (mes anterior al destino)
        if target_month == 1:
            source_month = 12
            source_year = target_year - 1
        else:
            source_month = target_month - 1
            source_year = target_year

        source_month_name = get_month_name(source_month)
        target_month_name = get_month_name(target_month)

        source_period = f"{source_month_name} {source_year}"
        target_period = f"{target_month_name} {target_year}"

        # Verificar que existan presupuestos en el mes origen
        source_budgets = Budget.objects.filter(
            user=self.request.user, month=source_month, year=source_year
        )

        if not source_budgets.exists():
            messages.warning(self.request, f"No hay presupuestos en {source_period} para copiar.")
            return HttpResponseRedirect(self.success_url)

        # Copiar presupuestos
        copied_count = 0
        skipped_count = 0
        skipped_categories = []

        for budget in source_budgets:
            # Verificar si ya existe en el período destino
            if not Budget.objects.filter(
                user=self.request.user,
                category=budget.category,
                month=target_month,
                year=target_year,
            ).exists():
                Budget.objects.create(
                    user=self.request.user,
                    category=budget.category,
                    month=target_month,
                    year=target_year,
                    amount=budget.amount,
                    alert_threshold=budget.alert_threshold,
                    notes=f"Copiado de {source_period}",
                )
                copied_count += 1
            else:
                skipped_count += 1
                skipped_categories.append(budget.category.name)

        # Mensaje detallado según resultado
        if copied_count > 0 and skipped_count == 0:
            messages.success(
                self.request,
                f"Se copiaron {copied_count} presupuesto(s) de {source_period} a {target_period}.",
            )
        elif copied_count > 0 and skipped_count > 0:
            messages.success(
                self.request,
                f"Se copiaron {copied_count} presupuesto(s) a {target_period}. "
                f"{skipped_count} ya existían y se omitieron ({', '.join(skipped_categories)}).",
            )
        else:
            messages.info(
                self.request,
                f"Todos los presupuestos de {source_period} ya existen en {target_period}.",
            )

        # Redirigir al período destino
        return HttpResponseRedirect(f"{self.success_url}?month={target_month}&year={target_year}")
