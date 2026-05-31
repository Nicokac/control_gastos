import csv
import logging

from django.contrib import messages
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.utils import timezone

from apps.categories.models import Category
from apps.core.views import (
    UserOwnedCreateView,
    UserOwnedDeleteView,
    UserOwnedDetailView,
    UserOwnedListView,
    UserOwnedUpdateView,
)

from .forms import IncomeFilterForm, IncomeForm
from .models import Income

logger = logging.getLogger(__name__)


class IncomeListView(UserOwnedListView):
    model = Income
    template_name = "income/income_list.html"
    context_object_name = "incomes"

    def get_queryset(self):
        qs = super().get_queryset().select_related("category", "category__parent")

        has_filters = any(
            key in self.request.GET
            for key in [
                "q",
                "month",
                "year",
                "category",
                "date_from",
                "date_to",
            ]
        )

        if has_filters:
            month = self.request.GET.get("month")
            year = self.request.GET.get("year")
        else:
            today = timezone.localdate()
            month = str(today.month)
            year = str(today.year)

        q = self.request.GET.get("q", "").strip()
        category = self.request.GET.get("category")

        if month:
            try:
                month_int = int(month)
                if 1 <= month_int <= 12:
                    qs = qs.filter(date__month=month_int)
            except ValueError:
                pass

        if year:
            try:
                year_int = int(year)
                if 1900 <= year_int <= 2100:
                    qs = qs.filter(date__year=year_int)
            except ValueError:
                pass

        if q:
            qs = qs.filter(
                Q(description__icontains=q)
                | Q(category__name__icontains=q)
                | Q(category__parent__name__icontains=q)
            )

        if category:
            try:
                category_int = int(category)
                if category_int > 0:
                    qs = qs.filter(category_id=category_int)
            except ValueError:
                pass

        order_by = self.request.GET.get("order_by", "date")
        direction = self.request.GET.get("dir", "desc")
        allowed_fields = {
            "date": "date",
            "category": "category__name",
            "description": "description",
            "amount": "amount_ars",
        }
        field = allowed_fields.get(order_by, "date")
        prefix = "-" if direction == "desc" else ""
        return qs.order_by(f"{prefix}{field}", "-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Si no hay filtros en GET, usar defaults para el formulario
        has_filters = any(
            key in self.request.GET
            for key in ["q", "month", "year", "category", "date_from", "date_to"]
        )

        today = timezone.localdate()

        if has_filters:
            form_data = self.request.GET
        else:
            form_data = {"month": today.month, "year": today.year}

        context["filter_form"] = IncomeFilterForm(form_data, user=self.request.user)
        context["has_active_filters"] = any(self.request.GET.get(key) for key in ["q", "category"])
        context["order_by"] = self.request.GET.get("order_by", "date")
        context["order_dir"] = self.request.GET.get("dir", "desc")

        total = self.object_list.aggregate(total=Sum("amount_ars"))["total"] or 0
        context["total"] = total

        category_summary = [
            {
                "name": row["category__name"],
                "parent": row["category__parent__name"] or "",
                "subtotal": row["subtotal"],
            }
            for row in self.object_list.values("category__name", "category__parent__name")
            .annotate(subtotal=Sum("amount_ars"))
            .order_by("-subtotal")
        ]
        context["category_summary"] = category_summary

        return context


class IncomeCreateView(UserOwnedCreateView):
    model = Income
    form_class = IncomeForm
    template_name = "income/income_form.html"
    success_url = reverse_lazy("income:list")

    def get_success_message(self):
        obj = self.object
        return f"Ingreso registrado: {obj.description} - {obj.formatted_amount}"

    def form_invalid(self, form):
        messages.error(
            self.request,
            "No pudimos guardar el ingreso. Revisá los campos marcados. Monto, categoría, fecha y descripción son obligatorios.",
        )
        return super().form_invalid(form)

    def get_success_url(self):
        if self.request.GET.get("recurring"):
            return reverse_lazy("recurring_income:list")
        return super().get_success_url()

    def form_valid(self, form):
        response = super().form_valid(form)
        recurring_pk = self.request.GET.get("recurring")
        if recurring_pk:
            try:
                from apps.recurring_income.models import RecurringIncome

                rec = RecurringIncome.objects.get(pk=recurring_pk, user=self.request.user)
                self.object.recurring = rec
                self.object.save(update_fields=["recurring"])
            except (RecurringIncome.DoesNotExist, ValueError):
                pass
        return response

    def get_initial(self):
        initial = super().get_initial()
        recurring_pk = self.request.GET.get("recurring")
        if recurring_pk:
            try:
                from apps.recurring_income.models import RecurringIncome

                rec = RecurringIncome.objects.get(pk=recurring_pk, user=self.request.user)
                initial["category"] = rec.category
                initial["description"] = rec.name
            except (RecurringIncome.DoesNotExist, ValueError):
                pass
        duplicate_pk = self.request.GET.get("duplicate")
        if duplicate_pk:
            try:
                source = Income.objects.get(pk=duplicate_pk, user=self.request.user)
                initial["category"] = source.category
                initial["description"] = source.description
                initial["amount"] = source.amount
                initial["currency"] = source.currency
                initial["exchange_rate"] = source.exchange_rate
            except (Income.DoesNotExist, ValueError):
                pass

        # Precargar última cotización USD usada por el usuario
        if not initial.get("exchange_rate"):
            last_usd = (
                Income.objects.filter(user=self.request.user, currency="USD")
                .order_by("-date", "-created_at")
                .values_list("exchange_rate", flat=True)
                .first()
            )
            if last_usd:
                initial["exchange_rate"] = last_usd

        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories_by_group"] = Category.get_categories_by_group(
            self.request.user, "INCOME"
        )
        recurring_pk = self.request.GET.get("recurring")
        if recurring_pk:
            try:
                from apps.recurring_income.models import RecurringIncome

                context["linked_recurring"] = RecurringIncome.objects.get(
                    pk=recurring_pk, user=self.request.user
                )
            except (RecurringIncome.DoesNotExist, ValueError):
                pass
        return context


class IncomeUpdateView(UserOwnedUpdateView):
    model = Income
    form_class = IncomeForm
    template_name = "income/income_form.html"
    success_url = reverse_lazy("income:list")

    def get_success_message(self):
        obj = self.object
        return f"Ingreso actualizado: {obj.description} - {obj.formatted_amount}"

    def form_invalid(self, form):
        messages.error(
            self.request,
            "No pudimos guardar el ingreso. Revisá los campos marcados.",
        )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories_by_group"] = Category.get_categories_by_group(
            self.request.user, "INCOME"
        )
        return context


class IncomeDeleteView(UserOwnedDeleteView):
    model = Income
    template_name = "income/income_confirm_delete.html"
    success_url = reverse_lazy("income:list")

    def get_success_message(self, obj):
        return f"Ingreso '{obj.description}' eliminado correctamente."


class IncomeDetailView(UserOwnedDetailView):
    model = Income
    template_name = "income/income_detail.html"
    context_object_name = "income"

    def get_queryset(self):
        return super().get_queryset().select_related("category")


class IncomeExportView(IncomeListView):
    """Exporta los ingresos filtrados como CSV, respetando los mismos filtros que la lista."""

    def get(self, request, *args, **kwargs):
        incomes = self.get_queryset().select_related("category", "category__parent")

        today = timezone.localdate()
        filename = f"ingresos {today.strftime('%d.%m.%Y')}.csv"
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response.write("﻿")  # BOM para compatibilidad con Excel

        writer = csv.writer(response)
        writer.writerow(
            [
                "Fecha",
                "Grupo",
                "Categoría",
                "Descripción",
                "Monto",
                "Moneda",
                "Tipo de cambio",
                "Monto ARS",
            ]
        )

        for income in incomes:
            cat = income.category
            grupo = cat.parent.name if cat.parent else cat.name
            categoria = cat.name if cat.parent else ""
            writer.writerow(
                [
                    income.date.strftime("%d/%m/%Y"),
                    grupo,
                    categoria,
                    income.description,
                    income.amount,
                    income.currency,
                    income.exchange_rate or "",
                    income.amount_ars,
                ]
            )

        return response
