from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.v1.pagination import ConfigurablePageNumberPagination
from apps.api.v1.serializers.expenses import ExpenseSerializer
from apps.categories.rules import learn_rule
from apps.expenses.models import Expense
from apps.expenses.quick_entry import QuickEntryError, parse_quick_expense, quick_expense_to_dict


class ExpenseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ExpenseSerializer
    pagination_class = ConfigurablePageNumberPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Expense.objects.none()

        qs = (
            Expense.objects.filter(user=self.request.user)
            .select_related("category", "category__parent")
            .order_by("-date", "-created_at")
        )
        month = self.request.query_params.get("month")
        year = self.request.query_params.get("year")
        category = self.request.query_params.get("category")

        if month:
            qs = qs.filter(date__month=month)
        if year:
            qs = qs.filter(date__year=year)
        if category:
            qs = qs.filter(category__pk=category)
        return qs

    @extend_schema(
        request=inline_serializer("QuickParseRequest", {"text": serializers.CharField()}),
        responses={200: dict, 400: dict},
        summary="Interpreta un gasto escrito en una línea (carga rápida), sin guardarlo",
    )
    @action(detail=False, methods=["post"], url_path="quick-parse")
    def quick_parse(self, request):
        try:
            parsed = parse_quick_expense(request.user, request.data.get("text", ""))
        except QuickEntryError as error:
            return Response({"ok": False, "error": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"ok": True, **quick_expense_to_dict(parsed)})

    @extend_schema(
        request=ExpenseSerializer,
        responses={201: dict, 400: dict},
        summary="Guarda el gasto de la carga rápida y aprende la regla si se corrigió la categoría",
    )
    @action(detail=False, methods=["post"], url_path="quick-create")
    def quick_create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        expense = serializer.save()

        learned = None
        if str(expense.category_id) != str(request.data.get("suggested_category") or ""):
            rule = learn_rule(request.user, expense.description, expense.category)
            if rule:
                learned = {"pattern": rule.pattern, "category_name": expense.category.name}
        return Response(
            {**serializer.data, "learned_rule": learned}, status=status.HTTP_201_CREATED
        )
