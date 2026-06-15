from decimal import Decimal

from django.urls import reverse
from django.utils import timezone

import pytest

from apps.expenses.forms import ExpenseFilterForm


@pytest.mark.django_db
class TestExpenseListContext:
    def test_expense_list_provides_expected_context_keys(
        self,
        client,
        user,
        expense_category_factory,
        expense_factory,
    ):
        client.force_login(user)

        cat = expense_category_factory(user, name="Comida")
        expense_factory(
            user,
            cat,
            amount=Decimal("100.00"),
            date=timezone.now().date(),
        )

        response = client.get(reverse("expenses:list"))

        assert response.status_code == 200

        assert "filter_form" in response.context
        assert "total" in response.context
        assert "payment_method_summary" in response.context

        assert isinstance(response.context["filter_form"], ExpenseFilterForm)
