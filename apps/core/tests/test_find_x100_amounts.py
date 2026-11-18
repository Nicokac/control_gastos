from datetime import timedelta
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.utils import timezone

import pytest

from apps.shared_expenses.models import SharedExpense


def _mark_edited(obj):
    type(obj).objects.filter(pk=obj.pk).update(
        created_at=timezone.now() - timedelta(days=2), updated_at=timezone.now()
    )


def _run(*args):
    out = StringIO()
    call_command("find_x100_amounts", *args, stdout=out)
    return out.getvalue()


@pytest.mark.django_db
class TestFindX100Amounts:
    def _history(self, factory, user, category, amounts):
        for amount in amounts:
            factory(user, category, amount=Decimal(amount))

    def test_detecta_gasto_editado_x100(self, user, expense_category, expense_factory):
        self._history(expense_factory, user, expense_category, ["8000", "9000", "8500"])
        broken = expense_factory(
            user, expense_category, amount=Decimal("850000"), description="Nafta"
        )
        _mark_edited(broken)

        output = _run()

        assert f"Gasto #{broken.pk}" in output
        assert "monto 850000.00 -> 8500" in output
        assert "Sospechosos: 1" in output

    def test_ignora_monto_alto_nunca_editado(self, user, expense_category, expense_factory):
        self._history(expense_factory, user, expense_category, ["8000", "9000"])
        expense_factory(user, expense_category, amount=Decimal("850000"))

        assert "Sospechosos: 0" in _run()

    def test_ignora_monto_con_decimales(self, user, expense_category, expense_factory):
        self._history(expense_factory, user, expense_category, ["8000", "9000"])
        _mark_edited(expense_factory(user, expense_category, amount=Decimal("850000.50")))

        assert "Sospechosos: 0" in _run()

    def test_ignora_monto_alto_coherente_con_la_categoria(
        self, user, expense_category, expense_factory
    ):
        self._history(expense_factory, user, expense_category, ["800000", "900000"])
        _mark_edited(expense_factory(user, expense_category, amount=Decimal("850000")))

        assert "Sospechosos: 0" in _run()

    def test_min_ratio_configurable(self, user, expense_category, expense_factory):
        self._history(expense_factory, user, expense_category, ["10000"])
        _mark_edited(expense_factory(user, expense_category, amount=Decimal("150000")))

        assert "Sospechosos: 0" in _run()
        assert "Sospechosos: 1" in _run("--min-ratio", "10")

    def test_filtra_por_usuario(self, user, other_user, expense_category_factory, expense_factory):
        for owner in (user, other_user):
            category = expense_category_factory(user=owner, name=f"Nafta {owner.pk}")
            self._history(expense_factory, owner, category, ["8000", "9000"])
            _mark_edited(expense_factory(owner, category, amount=Decimal("850000")))

        output = _run("--user", user.email)

        assert user.email in output
        assert other_user.email not in output
        assert "Sospechosos: 1" in output

    def test_detecta_ingreso(self, user, income_category, income_factory):
        self._history(income_factory, user, income_category, ["500000", "520000"])
        broken = income_factory(user, income_category, amount=Decimal("51000000"))
        _mark_edited(broken)

        assert f"Ingreso #{broken.pk}" in _run()

    def test_detecta_gasto_compartido(self, user, expense_category):
        for amount in ["20000", "22000"]:
            SharedExpense.objects.create(
                user=user,
                date=timezone.localdate(),
                description="Super",
                amount=Decimal(amount),
                currency="ARS",
                category=expense_category,
            )
        broken = SharedExpense.objects.create(
            user=user,
            date=timezone.localdate(),
            description="Super",
            amount=Decimal("2100000"),
            currency="ARS",
            category=expense_category,
        )
        _mark_edited(broken)

        assert f"Gasto compartido #{broken.pk}" in _run()

    def test_detecta_meta_de_ahorro(self, user, saving_factory):
        saving_factory(user, name="Auto", target_amount=Decimal("150000"))
        broken = saving_factory(user, name="Vacaciones", target_amount=Decimal("15000000"))
        _mark_edited(broken)

        assert f"Meta de ahorro #{broken.pk}" in _run()

    def test_editado_sin_referencia_se_lista_aparte(self, user, saving_factory):
        alone = saving_factory(user, name="Única", target_amount=Decimal("15000000"))
        _mark_edited(alone)

        output = _run()

        assert "Sospechosos: 0" in output
        assert "sin otros registros para comparar (1)" in output
        assert f"Meta de ahorro #{alone.pk}" in output
