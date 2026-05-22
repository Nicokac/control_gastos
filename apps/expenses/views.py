import csv
import logging

from django.contrib import messages
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.utils import timezone

from apps.categories.models import Category
from apps.core.constants import ExpenseType, PaymentMethod
from apps.core.utils import get_month_date_range_exclusive
from apps.core.views import (
    UserOwnedCreateView,
    UserOwnedDeleteView,
    UserOwnedDetailView,
    UserOwnedListView,
    UserOwnedUpdateView,
)

from .forms import ExpenseFilterForm, ExpenseForm
from .models import Expense

logger = logging.getLogger(__name__)


class ExpenseListView(UserOwnedListView):
    model = Expense
    template_name = "expenses/expense_list.html"
    context_object_name = "expenses"

    def get_queryset(self):
        qs = super().get_queryset().select_related("category", "category__parent", "saving")

        has_filters = any(
            key in self.request.GET
            for key in [
                "q",
                "month",
                "year",
                "category",
                "subcategory",
                "date_from",
                "date_to",
                "payment_method",
                "expense_type",
                "amount_min",
                "amount_max",
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
        subcategory = self.request.GET.get("subcategory")
        payment_method = self.request.GET.get("payment_method")
        expense_type = self.request.GET.get("expense_type")

        # ✅ Mes/año -> rango [start, end)
        if month and year:
            try:
                month_int = int(month)
                year_int = int(year)
                if 1 <= month_int <= 12 and 1900 <= year_int <= 2100:
                    start, end = get_month_date_range_exclusive(month_int, year_int)
                    qs = qs.filter(date__gte=start, date__lt=end)
            except ValueError:
                pass
        else:
            # Si viene solo year, mantenemos comportamiento actual
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
        if subcategory:
            # subcategoría específica tiene prioridad sobre el grupo
            qs = qs.filter(category_id=subcategory)
        elif category:
            # category contiene el pk de un grupo (parent); filtramos sus subcategorías
            qs = qs.filter(category__parent_id=category)
        if payment_method:
            qs = qs.filter(payment_method=payment_method)
        if expense_type:
            qs = qs.filter(expense_type=expense_type)

        try:
            amount_min = self.request.GET.get("amount_min")
            if amount_min:
                qs = qs.filter(amount_ars__gte=amount_min)
        except (ValueError, TypeError):
            pass
        try:
            amount_max = self.request.GET.get("amount_max")
            if amount_max:
                qs = qs.filter(amount_ars__lte=amount_max)
        except (ValueError, TypeError):
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
        qs = qs.order_by(f"{prefix}{field}", "-created_at")
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        has_filters = any(
            key in self.request.GET
            for key in [
                "q",
                "month",
                "year",
                "category",
                "subcategory",
                "date_from",
                "date_to",
                "payment_method",
                "expense_type",
            ]
        )

        if has_filters:
            form_data = self.request.GET
        else:
            today = timezone.localdate()
            form_data = {"month": today.month, "year": today.year}

        context["filter_form"] = ExpenseFilterForm(form_data, user=self.request.user)
        context["has_active_filters"] = any(
            self.request.GET.get(key)
            for key in [
                "q",
                "category",
                "subcategory",
                "payment_method",
                "expense_type",
                "amount_min",
                "amount_max",
            ]
        )
        context["order_by"] = self.request.GET.get("order_by", "date")
        context["order_dir"] = self.request.GET.get("dir", "desc")

        qs = self.object_list

        total = qs.aggregate(total=Sum("amount_ars"))["total"] or 0
        context["total"] = total

        expense_type_labels = dict(ExpenseType.choices)
        type_classified = qs.exclude(expense_type="").aggregate(s=Sum("amount_ars"))["s"] or 0
        type_unclassified = (total - type_classified) if total else 0
        expense_type_summary = [
            {
                "label": expense_type_labels.get(row["expense_type"], row["expense_type"]),
                "subtotal": row["subtotal"],
            }
            for row in qs.exclude(expense_type="")
            .values("expense_type")
            .annotate(subtotal=Sum("amount_ars"))
            .order_by("expense_type")
        ]
        if type_unclassified > 0:
            expense_type_summary.append({"label": "Sin clasificar", "subtotal": type_unclassified})
        context["expense_type_summary"] = expense_type_summary

        payment_method_labels = dict(PaymentMethod.choices)
        method_classified = qs.exclude(payment_method="").aggregate(s=Sum("amount_ars"))["s"] or 0
        method_unclassified = (total - method_classified) if total else 0
        payment_method_summary = [
            {
                "label": payment_method_labels.get(row["payment_method"], row["payment_method"]),
                "subtotal": row["subtotal"],
            }
            for row in qs.exclude(payment_method="")
            .values("payment_method")
            .annotate(subtotal=Sum("amount_ars"))
            .order_by("payment_method")
        ]
        if method_unclassified > 0:
            payment_method_summary.append(
                {"label": "Sin clasificar", "subtotal": method_unclassified}
            )
        context["payment_method_summary"] = payment_method_summary

        category_summary = [
            {
                "name": row["category__name"],
                "parent": row["category__parent__name"] or "",
                "subtotal": row["subtotal"],
                "category_pk": row["category_id"],
            }
            for row in qs.select_related("category__parent")
            .values("category_id", "category__name", "category__parent__name")
            .annotate(subtotal=Sum("amount_ars"))
            .order_by("-subtotal")
        ]
        context["category_summary"] = category_summary

        return context


class ExpenseCreateView(UserOwnedCreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = "expenses/expense_form.html"
    success_url = reverse_lazy("expenses:list")

    def get_success_url(self):
        if self.request.GET.get("recurring") or self.request.POST.get("recurring"):
            return reverse_lazy("recurring:list")
        return super().get_success_url()

    def get_success_message(self):
        obj = self.object
        return f"Gasto registrado: {obj.description} - {obj.formatted_amount}"

    def form_invalid(self, form):
        messages.error(
            self.request,
            "No pudimos guardar el gasto. Revisá los campos marcados. Monto, categoría y fecha son obligatorios.",
        )
        return super().form_invalid(form)

    def get_initial(self):
        initial = super().get_initial()
        recurring_pk = self.request.GET.get("recurring")
        if recurring_pk:
            try:
                from apps.recurring.models import RecurringExpense

                recurring = RecurringExpense.objects.get(pk=recurring_pk, user=self.request.user)
                initial["recurring"] = recurring.pk
                initial["category"] = recurring.category
                initial["description"] = recurring.name
            except (RecurringExpense.DoesNotExist, ValueError):
                pass

        duplicate_pk = self.request.GET.get("duplicate")
        if duplicate_pk:
            try:
                source = Expense.objects.get(pk=duplicate_pk, user=self.request.user)
                initial["category"] = source.category
                initial["description"] = source.description
                initial["amount"] = source.amount
                initial["currency"] = source.currency
                initial["exchange_rate"] = source.exchange_rate
                initial["payment_method"] = source.payment_method
                initial["expense_type"] = source.expense_type
            except (Expense.DoesNotExist, ValueError):
                pass

        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories_by_group"] = Category.get_categories_by_group(
            self.request.user, "EXPENSE"
        )
        recurring_pk = self.request.GET.get("recurring")
        if recurring_pk:
            try:
                from apps.recurring.models import RecurringExpense

                context["linked_recurring"] = RecurringExpense.objects.get(
                    pk=recurring_pk, user=self.request.user
                )
            except (RecurringExpense.DoesNotExist, ValueError):
                pass
        return context


class ExpenseUpdateView(UserOwnedUpdateView):
    model = Expense
    form_class = ExpenseForm
    template_name = "expenses/expense_form.html"
    success_url = reverse_lazy("expenses:list")

    def get_success_message(self):
        obj = self.object
        return f"Gasto actualizado: {obj.description} - {obj.formatted_amount}"

    def form_invalid(self, form):
        messages.error(
            self.request,
            "No pudimos guardar el gasto. Revisá los campos marcados.",
        )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories_by_group"] = Category.get_categories_by_group(
            self.request.user, "EXPENSE"
        )
        return context


class ExpenseDeleteView(UserOwnedDeleteView):
    model = Expense
    template_name = "expenses/expense_confirm_delete.html"
    success_url = reverse_lazy("expenses:list")

    def get_success_message(self, obj):
        return f"Gasto '{obj.description}' eliminado correctamente."


class ExpenseDetailView(UserOwnedDetailView):
    model = Expense
    template_name = "expenses/expense_detail.html"
    context_object_name = "expense"

    def get_queryset(self):
        return super().get_queryset().select_related("category", "saving")


class ExpenseExportView(ExpenseListView):
    """Exporta los gastos filtrados como CSV, respetando los mismos filtros que la lista."""

    def get(self, request, *args, **kwargs):
        expenses = self.get_queryset().select_related("category", "category__parent")

        today = timezone.localdate()
        filename = f"gastos {today.strftime('%d.%m.%Y')}.csv"
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response.write("﻿")  # BOM para compatibilidad con Excel

        writer = csv.writer(response)
        writer.writerow(
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
                "Tipo de gasto",
            ]
        )

        expense_type_labels = dict(ExpenseType.choices)
        payment_method_labels = dict(PaymentMethod.choices)

        for expense in expenses:
            cat = expense.category
            grupo = cat.parent.name if cat.parent else cat.name
            subcategoria = cat.name if cat.parent else ""
            writer.writerow(
                [
                    expense.date.strftime("%d/%m/%Y"),
                    grupo,
                    subcategoria,
                    expense.description,
                    expense.amount,
                    expense.currency,
                    expense.exchange_rate or "",
                    expense.amount_ars,
                    payment_method_labels.get(expense.payment_method, "")
                    if expense.payment_method
                    else "",
                    expense_type_labels.get(expense.expense_type, "")
                    if expense.expense_type
                    else "",
                ]
            )

        return response
