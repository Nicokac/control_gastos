"""Vistas para gestión de gastos."""

import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.categories.models import Category

from .forms import ExpenseFilterForm, ExpenseForm
from .models import Expense

logger = logging.getLogger("apps.expenses")


# Create your views here.
class ExpenseListView(LoginRequiredMixin, ListView):
    """Lista de gastos del usuario con filtros."""

    model = Expense
    template_name = "expenses/expense_list.html"
    context_object_name = "expenses"
    paginate_by = 20

    def get_queryset(self):
        """Filtra gastos del usuario actual."""
        queryset = Expense.objects.filter(user=self.request.user).select_related("category")

        # Aplicar filtros
        month = self.request.GET.get("month")
        year = self.request.GET.get("year")
        category = self.request.GET.get("category")

        try:
            if month:
                month = int(month)
                if 1 <= month <= 12:
                    queryset = queryset.filter(date__month=month)

            if year:
                year = int(year)
                if 1900 <= year <= 2100:
                    queryset = queryset.filter(date__year=year)

            if category:
                category = int(category)
                queryset = queryset.filter(category_id=category)
        except (ValueError, TypeError) as e:
            logger.debug(f"ExpenseListView: filtro inválido ignorado - {e}")

        return queryset

    def get_context_data(self, **kwargs):
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)

        # Formulario de filtros
        context["filter_form"] = ExpenseFilterForm(
            data=self.request.GET or None, user=self.request.user
        )

        # Total del período filtrado
        queryset = self.get_queryset()
        context["total"] = queryset.aggregate(total=Sum("amount_ars"))["total"] or 0

        # Mes y año actual para defaults
        today = timezone.now().date()
        context["current_month"] = today.month
        context["current_year"] = today.year

        return context


class ExpenseCreateView(LoginRequiredMixin, CreateView):
    """Crear nuevo gasto con formulario optimizado."""

    model = Expense
    form_class = ExpenseForm
    template_name = "expenses/expense_form.html"
    success_url = reverse_lazy("expenses:list")

    def get_form_kwargs(self):
        """Päsa el usuario al formulario."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        """Agrega categorías para los botones visuales."""
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.get_expense_categories(self.request.user)
        context["is_edit"] = False
        return context

    def form_valid(self, form):
        """Guarda y muestra mensaje de éxito."""
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"Gasto registrado: {self.object.description} - {self.object.formatted_amount}",
        )
        return response

    def form_invalid(self, form):
        """Muestra errores."""
        messages.error(self.request, "Corregí los errores del formulario.")
        return super().form_invalid(form)


class ExpenseUpdateView(LoginRequiredMixin, UpdateView):
    """Editar gasto existente."""

    model = Expense
    form_class = ExpenseForm
    template_name = "expenses/expense_form.html"
    success_url = reverse_lazy("expenses:list")

    def get_queryset(self):
        """Solo permite editar gastos propios."""
        return Expense.objects.filter(user=self.request.user)

    def get_form_kwargs(self):
        """Pasa el usuario al formulario."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        """Agrega categorías para los botones visuales."""
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.get_expense_categories(self.request.user)
        context["is_edit"] = True
        return context

    def form_valid(self, form):
        """Guarda y muestra mensaje de éxito."""
        response = super().form_valid(form)
        messages.success(self.request, "Gasto actualizado correctamente.")
        return response


class ExpenseDeleteView(LoginRequiredMixin, DeleteView):
    """Eliminar gasto (soft delete)."""

    model = Expense
    template_name = "expenses/expense_confirm_delete.html"
    success_url = reverse_lazy("expenses:list")

    def get_queryset(self):
        """Solo permite eliminar gastos propios."""
        return Expense.objects.filter(user=self.request.user)

    def form_valid(self, form):
        """Realiza soft delete."""
        self.object = self.get_object()
        self.object.soft_delete()
        messages.success(self.request, "Gasto eliminado correctamente.")
        from django.http import HttpResponseRedirect

        return HttpResponseRedirect(self.success_url)


class ExpenseDetailView(LoginRequiredMixin, DetailView):
    """Ver detalle de un gasto."""

    model = Expense
    template_name = "expenses/expense_detail.html"
    context_object_name = "expense"

    def get_queryset(self):
        """Solo permite ver gastos propios."""
        return Expense.objects.filter(user=self.request.user).select_related("category")
