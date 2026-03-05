from decimal import Decimal

from django.urls import reverse
from django.utils import timezone

import pytest


@pytest.mark.django_db
class TestExpenseListQueries:
    def test_expense_list_query_count_is_bounded(
        self,
        client,
        django_assert_num_queries,
        user,
        expense_category_factory,
        expense_factory,
    ):
        """
        El listado NO debe degradar a N+1.
        Este test busca detectar regresiones en el conteo de queries.
        """
        client.force_login(user)
        today = timezone.now().date()

        cat = expense_category_factory(user, name="Cat Test Queries")
        for _ in range(30):
            expense_factory(user, cat, amount=Decimal("10.00"), date=today)

        url = reverse("expenses:list")

        # Baseline actual medido: 4 queries (listado + aggregates).
        with django_assert_num_queries(4):
            resp = client.get(url)

        assert resp.status_code == 200
