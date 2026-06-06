from django.utils import timezone

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.v1.pagination import ConfigurablePageNumberPagination
from apps.api.v1.serializers.recurring_income import RecurringIncomeSerializer
from apps.recurring_income.models import RecurringIncome


class RecurringIncomeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = RecurringIncomeSerializer
    pagination_class = ConfigurablePageNumberPagination

    def get_queryset(self):
        return (
            RecurringIncome.objects.filter(user=self.request.user)
            .select_related("category", "category__parent")
            .order_by("expected_day", "name")
        )

    @action(detail=True, methods=["post"], url_path="mark-received")
    def mark_received(self, request, pk=None):
        from apps.income.models import Income

        rec = self.get_object()
        today = timezone.localdate()

        if rec.is_collected_in(today.month, today.year):
            return Response(
                {"detail": "Este ingreso ya fue registrado este mes."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        amount = request.data.get("amount")
        if not amount:
            last = rec.last_income
            amount = last.amount if last else None
        if not amount:
            return Response(
                {"detail": "Indicá el monto del cobro."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        income = Income.objects.create(
            user=request.user,
            date=today,
            category=rec.category,
            description=rec.name,
            amount=amount,
            currency="ARS",
            recurring=rec,
        )
        return Response(
            {"detail": "Cobro registrado.", "income_id": income.pk}, status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=["get"])
    def pending(self, request):
        today = timezone.localdate()
        items = [
            rec
            for rec in self.get_queryset().filter(is_active=True)
            if rec.status_for(today.month, today.year) in ("pending", "overdue")
        ]
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)
