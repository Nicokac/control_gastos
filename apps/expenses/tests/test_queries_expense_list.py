from decimal import Decimal

from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

import pytest

from apps.expenses.views import ExpenseListView


@pytest.mark.django_db
def test_expense_list_query_count_is_stable_requestfactory(
    django_assert_max_num_queries,
    user,
    expense_category_factory,
    expense_factory,
):
    # Arrange
    cat = expense_category_factory(user, name="Cat 1")
    expense_factory(user, cat, amount=Decimal("10.00"), date=timezone.now().date())

    rf = RequestFactory()
    request = rf.get(reverse("expenses:list"))
    request.user = user

    # Act + Assert
    # Baseline actual:
    # 1) count paginación
    # 2) total del período
    # 3) resumen por tipo
    # 4) resumen por método de pago
    # 5) categorías del filter_form
    # 6) listado paginado
    # 7+) queries adicionales por categorías agrupadas y contexto extra
    with django_assert_max_num_queries(10):
        response = ExpenseListView.as_view()(request)
        response.render()  # fuerza template + queryset

    assert response.status_code == 200
