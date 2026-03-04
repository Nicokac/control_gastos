from decimal import Decimal

from django.urls import reverse
from django.utils import timezone

import pytest


@pytest.mark.django_db
class TestExpenseListQueries:
    def test_expense_list_query_count_is_stable(
        self,
        client,
        django_assert_num_queries,
        user,
        expense_category_factory,
        expense_factory,
    ):
        # Arrange
        client.force_login(user)

        cat = expense_category_factory(user, name="Cat 1")
        expense_factory(user, cat, amount=Decimal("10.00"), date=timezone.now().date())

        url = reverse("expenses:list")

        # Act + Assert
        with django_assert_num_queries(4):
            resp = client.get(url)

        assert resp.status_code == 200
