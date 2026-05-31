from decimal import Decimal

from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

import pytest

from apps.savings.models import MovementType


@pytest.mark.django_db
class TestDashboardQueries:
    def test_dashboard_query_count_is_reasonable_and_top_savings_ordered(
        self,
        client,
        django_assert_max_num_queries,
        user,
        expense_category_factory,
        income_category_factory,
        expense_factory,
        income_factory,
        saving_factory,
        saving_movement_factory,
    ):
        # Arrange
        client.force_login(user)

        # Categorías mínimas (dashboard usa gastos/ingresos para aggregates y últimas transacciones)
        exp_cat = expense_category_factory(user, name="Cat Expense 1")
        inc_cat = income_category_factory(user, name="Cat Income 1")

        today = timezone.now().date()

        expense_factory(user, exp_cat, amount=Decimal("10.00"), date=today)
        income_factory(user, inc_cat, amount=Decimal("20.00"), date=today)

        # Savings: creamos 3 activas con progreso distinto para validar orden
        s1 = saving_factory(
            user=user,
            status="ACTIVE",
            target_amount=Decimal("100.00"),
            current_amount=Decimal("10.00"),  # 10%
        )
        saving_factory(
            user=user,
            status="ACTIVE",
            target_amount=Decimal("100.00"),
            current_amount=Decimal("60.00"),  # 60%
        )
        saving_factory(
            user=user,
            status="ACTIVE",
            target_amount=Decimal("100.00"),
            current_amount=Decimal("30.00"),  # 30%
        )

        # Movimiento para que exista query de depósitos del mes
        saving_movement_factory(
            saving=s1,
            type=MovementType.DEPOSIT,
            amount=Decimal("5.00"),
        )

        url = reverse("reports:dashboard")

        # Act + Assert (anti N+1): +3 queries por _get_monthly_evolution
        with django_assert_max_num_queries(17):
            resp = client.get(url)

        assert resp.status_code == 200

        # Validar que "top_savings" venga ordenado por mayor progreso
        top = resp.context["top_savings"]
        assert len(top) <= 3
        if len(top) >= 2:
            progresses = [s.progress_percentage for s in top]
            assert progresses == sorted(progresses, reverse=True)

    @pytest.mark.django_db
    def test_dashboard_query_count_is_stable(self, django_assert_max_num_queries, user):
        """
        Baseline: el dashboard debe mantenerse estable en cantidad de queries.
        Usamos RequestFactory para NO contar session/auth middleware.
        """
        rf = RequestFactory()
        request = rf.get("/reports/dashboard/")
        request.user = user

        from apps.reports.views import DashboardView

        with django_assert_max_num_queries(15):
            response = DashboardView.as_view()(request)

        assert response.status_code == 200
