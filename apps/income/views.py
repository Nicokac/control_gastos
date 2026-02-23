import logging

from django.db.models import Sum
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
        qs = super().get_queryset().select_related("category")
        month = self.request.GET.get("month")
        year = self.request.GET.get("year")
        category = self.request.GET.get("category")

        if month:
            try:
                month = int(month)
                if 1 <= month <= 12:
                    qs = qs.filter(date__month=month)
            except ValueError:
                pass

        if year:
            try:
                year = int(year)
                if 1900 <= year <= 2100:
                    qs = qs.filter(date__year=year)
            except ValueError:
                pass

        if category:
            try:
                category = int(category)
                if category > 0:
                    qs = qs.filter(category_id=category)
            except ValueError:
                pass

        return qs.order_by("-date", "-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = IncomeFilterForm(self.request.GET, user=self.request.user)
        total = self.get_queryset().aggregate(total=Sum("amount_ars"))["total"] or 0
        context["total_amount"] = total

        today = timezone.now().date()
        context["current_month"] = today.month
        context["current_year"] = today.year
        return context


class IncomeCreateView(UserOwnedCreateView):
    model = Income
    form_class = IncomeForm
    template_name = "income/income_form.html"
    success_url = "/income/"

    def get_success_message(self):
        obj = self.object
        return f"Ingreso registrado: {obj.description} - {obj.formatted_amount}"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.get_income_categories(self.request.user)
        return context


class IncomeUpdateView(UserOwnedUpdateView):
    model = Income
    form_class = IncomeForm
    template_name = "income/income_form.html"
    success_url = "/income/"

    def get_success_message(self):
        obj = self.object
        return f"Ingreso actualizado: {obj.description} - {obj.formatted_amount}"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.get_income_categories(self.request.user)
        return context


class IncomeDeleteView(UserOwnedDeleteView):
    model = Income
    template_name = "income/income_confirm_delete.html"
    success_url = "/income/"

    def get_success_message(self, obj):
        return f"Ingreso '{obj.description}' eliminado correctamente."


class IncomeDetailView(UserOwnedDetailView):
    model = Income
    template_name = "income/income_detail.html"
    context_object_name = "income"

    def get_queryset(self):
        return super().get_queryset().select_related("category")
