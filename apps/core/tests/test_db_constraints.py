from decimal import Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone

import pytest

from apps.categories.models import Category
from apps.core.constants import CategoryType, Currency
from apps.expenses.models import Expense
from apps.income.models import Income
from apps.savings.models import MovementType, Saving, SavingMovement

pytestmark = pytest.mark.django_db


class TestDbConstraints:
    def test_expense_amount_positive_db_constraint_blocks_update(self, user):
        # category expense mínima
        cat = Category.objects.create(user=user, name="CAT_TEST_EXPENSE", type=CategoryType.EXPENSE)
        e = Expense.objects.create(
            user=user,
            category=cat,
            date=timezone.now().date(),
            amount=Decimal("1.00"),
            description="TEST_EXPENSE_OK",
        )

        with pytest.raises(IntegrityError), transaction.atomic():
            Expense.objects.filter(pk=e.pk).update(amount=Decimal("0.00"))

    def test_income_amount_positive_db_constraint_blocks_update(self, user):
        cat = Category.objects.create(user=user, name="CAT_TEST_INCOME", type=CategoryType.INCOME)
        i = Income.objects.create(
            user=user,
            category=cat,
            date=timezone.now().date(),
            amount=Decimal("1.00"),
            description="TEST_INCOME_OK",
        )

        with pytest.raises(IntegrityError), transaction.atomic():
            Income.objects.filter(pk=i.pk).update(amount=Decimal("0.00"))

    def test_saving_target_amount_positive_db_constraint_blocks_update(self, user):
        s = Saving.objects.create(
            user=user,
            name="TEST_SAVING_OK",
            target_amount=Decimal("10.00"),
            current_amount=Decimal("0.00"),
            currency=Currency.ARS,
        )

        with pytest.raises(IntegrityError), transaction.atomic():
            Saving.objects.filter(pk=s.pk).update(target_amount=Decimal("0.00"))

    def test_saving_current_amount_non_negative_db_constraint_blocks_update(self, user):
        s = Saving.objects.create(
            user=user,
            name="TEST_SAVING_OK_2",
            target_amount=Decimal("10.00"),
            current_amount=Decimal("0.00"),
            currency=Currency.ARS,
        )

        with pytest.raises(IntegrityError), transaction.atomic():
            Saving.objects.filter(pk=s.pk).update(current_amount=Decimal("-1.00"))

    def test_saving_movement_amount_positive_db_constraint_blocks_update(self, user):
        s = Saving.objects.create(
            user=user,
            name="TEST_SAVING_MOV_OK",
            target_amount=Decimal("10.00"),
            current_amount=Decimal("0.00"),
            currency=Currency.ARS,
        )
        m = SavingMovement.objects.create(
            saving=s,
            type=MovementType.DEPOSIT,
            amount=Decimal("1.00"),
            description="TEST_MOV_OK",
        )

        with pytest.raises(IntegrityError), transaction.atomic():
            SavingMovement.objects.filter(pk=m.pk).update(amount=Decimal("0.00"))
