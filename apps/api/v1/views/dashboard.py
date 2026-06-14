from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils import get_financial_period
from apps.expenses.models import Expense
from apps.income.models import Income
from apps.recurring.models import RecurringExpense
from apps.savings.models import Saving, SavingStatus


@extend_schema(tags=["dashboard"], responses={(200, "application/json"): OpenApiTypes.OBJECT})
class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.localdate()

        try:
            month = int(request.query_params.get("month", today.month))
            year = int(request.query_params.get("year", today.year))
        except (ValueError, TypeError):
            month, year = today.month, today.year

        month = max(1, min(month, 12))
        year = max(2020, year)

        total_expenses = Expense.objects.filter(
            user=user, date__month=month, date__year=year
        ).aggregate(total=Sum("amount_ars"))["total"] or Decimal("0")

        total_income = Income.objects.filter(
            user=user, date__month=month, date__year=year
        ).aggregate(total=Sum("amount_ars"))["total"] or Decimal("0")

        balance = total_income - total_expenses

        expenses_by_category = list(
            Expense.objects.filter(user=user, date__month=month, date__year=year)
            .values("category__id", "category__name", "category__color", "category__icon")
            .annotate(total=Sum("amount_ars"))
            .order_by("-total")
        )

        income_by_category = list(
            Income.objects.filter(user=user, date__month=month, date__year=year)
            .values("category__id", "category__name", "category__color", "category__icon")
            .annotate(total=Sum("amount_ars"))
            .order_by("-total")
        )

        savings = Saving.objects.filter(user=user, status=SavingStatus.ACTIVE).values(
            "id", "name", "target_amount", "current_amount", "currency"
        )
        savings_progress = [
            {
                **s,
                "progress_percentage": round(
                    float(s["current_amount"]) / float(s["target_amount"]) * 100, 1
                )
                if s["target_amount"] > 0
                else 0,
            }
            for s in savings
        ]

        all_recurring = list(
            RecurringExpense.objects.filter(user=user, is_active=True).select_related("category")
        )
        total_recurring = len(all_recurring)
        pending_recurring = [
            {
                "id": rec.pk,
                "name": rec.name,
                "due_day": rec.due_day,
                "status": rec.status_for(month, year),
                "last_amount": str(rec.last_expense.amount_ars) if rec.last_expense else None,
            }
            for rec in all_recurring
            if rec.status_for(month, year) in ("pending", "overdue")
        ]

        recent_expenses = list(
            Expense.objects.filter(user=user)
            .select_related("category")
            .order_by("-date", "-created_at")
            .values(
                "id",
                "date",
                "description",
                "amount_ars",
                "category__name",
                "category__color",
                "category__icon",
            )[:5]
        )
        recent_income = list(
            Income.objects.filter(user=user)
            .select_related("category")
            .order_by("-date", "-created_at")
            .values(
                "id",
                "date",
                "description",
                "amount_ars",
                "category__name",
                "category__color",
                "category__icon",
            )[:5]
        )

        # Proyección de cierre de período (solo período actual, mínimo 3 días)
        is_current_period = month == today.month and year == today.year
        projection_available = False
        projected_expense = None
        projected_balance = None

        if is_current_period:
            start_day = getattr(user, "financial_month_start_day", 1)
            fin_start, fin_end = get_financial_period(month, year, start_day)
            period_total_days = (fin_end - fin_start).days
            if fin_start <= today < fin_end:
                period_day = (today - fin_start).days + 1
            else:
                period_day = period_total_days
            if period_day >= 3 and period_total_days > 0 and total_expenses > 0:
                daily_rate = total_expenses / period_day
                projected_expense = daily_rate * period_total_days
                projected_balance = total_income - projected_expense
                projection_available = True

        return Response(
            {
                "month": month,
                "year": year,
                "total_expenses": str(total_expenses),
                "total_income": str(total_income),
                "balance": str(balance),
                "expenses_by_category": [
                    {
                        "category_id": e["category__id"],
                        "category_name": e["category__name"],
                        "category_color": e["category__color"],
                        "category_icon": e["category__icon"],
                        "total": str(e["total"]),
                    }
                    for e in expenses_by_category
                ],
                "income_by_category": [
                    {
                        "category_id": e["category__id"],
                        "category_name": e["category__name"],
                        "category_color": e["category__color"],
                        "category_icon": e["category__icon"],
                        "total": str(e["total"]),
                    }
                    for e in income_by_category
                ],
                "savings_progress": savings_progress,
                "total_recurring": total_recurring,
                "pending_recurring": pending_recurring,
                "recent_transactions": {
                    "expenses": recent_expenses,
                    "income": recent_income,
                },
                "projection_available": projection_available,
                "projected_expense": str(projected_expense)
                if projected_expense is not None
                else None,
                "projected_balance": str(projected_balance)
                if projected_balance is not None
                else None,
            }
        )
