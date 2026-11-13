from decimal import Decimal

from django.urls import reverse

import pytest

from apps.categories.models import Category
from apps.core.constants import CategoryType
from apps.core.utils import DONUT_OTHERS_COLOR, split_donut_segments

PALETTE = [
    "#dc3545",
    "#fd7e14",
    "#ffc107",
    "#28a745",
    "#20c997",
    "#0dcaf0",
    "#0d6efd",
    "#6610f2",
    "#d63384",
    "#6c757d",
]


class TestSplitDonutSegments:
    def test_segments_under_three_percent_go_to_others(self):
        main, others = split_donut_segments([400, 200, 150, 100, 60, 40, 25, 15, 10], lambda x: x)

        assert main == [400, 200, 150, 100, 60, 40]
        assert others == [25, 15, 10]

    def test_at_most_seven_own_segments(self):
        main, others = split_donut_segments([10] * 10, lambda x: x)

        assert len(main) == 7
        assert len(others) == 3

    def test_empty_and_zero_totals(self):
        assert split_donut_segments([], lambda x: x) == ([], [])
        assert split_donut_segments([0, 0], lambda x: x) == ([], [0, 0])


@pytest.mark.django_db
class TestDonutSameOnDashboardAndExpenseList:
    def test_dashboard_and_expense_list_group_others_the_same_way(
        self, authenticated_client, user, expense_category_factory, expense_factory
    ):
        amounts = [400, 200, 150, 100, 60, 40, 25, 15, 10]
        for index, amount in enumerate(amounts):
            group = Category.objects.create(
                name=f"Grupo {index}",
                type=CategoryType.EXPENSE,
                is_system=True,
                user=None,
                parent=None,
                color=PALETTE[index],
            )
            sub = expense_category_factory(user=user, parent=group, name=f"Sub {index}")
            expense_factory(user, sub, amount=Decimal(amount))

        dashboard = authenticated_client.get(reverse("reports:dashboard")).context
        expense_list = authenticated_client.get(reverse("expenses:list")).context

        expected_labels = [f"Grupo {i}" for i in range(6)] + ["Otros"]
        assert dashboard["chart_labels"] == expected_labels
        assert expense_list["donut_labels"] == expected_labels
        assert dashboard["chart_data"] == expense_list["donut_data"]
        assert (
            dashboard["chart_colors"][-1] == expense_list["donut_colors"][-1] == DONUT_OTHERS_COLOR
        )
