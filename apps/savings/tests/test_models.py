"""
Tests para los modelos Saving y SavingMovement.
"""

from decimal import Decimal

import pytest

from apps.savings.models import Saving, SavingMovement, SavingStatus


@pytest.mark.django_db
class TestSavingModel:
    """Tests para el modelo Saving."""

    def test_create_saving(self, user):
        """Verifica creación de meta de ahorro."""
        saving = Saving.objects.create(
            user=user,
            name="Vacaciones",
            target_amount=Decimal("50000.00"),
            current_amount=Decimal("0.00"),
        )

        assert saving.pk is not None
        assert saving.name == "Vacaciones"
        assert saving.target_amount == Decimal("50000.00")
        assert saving.current_amount == Decimal("0.00")

    def test_saving_default_status(self, saving):
        """Verifica estado por defecto."""
        assert saving.status == SavingStatus.ACTIVE

    def test_saving_str(self, saving):
        """Verifica representación string."""
        result = str(saving)

        assert saving.name in result

    def test_saving_progress_percentage_zero(self, user, saving_factory):
        """Verifica porcentaje de progreso en cero."""
        saving = saving_factory(user, current_amount=Decimal("0.00"))

        assert saving.progress_percentage == 0

    def test_saving_progress_percentage_partial(self, user, saving_factory):
        """Verifica porcentaje de progreso parcial."""
        saving = saving_factory(
            user, target_amount=Decimal("10000.00"), current_amount=Decimal("2500.00")
        )

        assert saving.progress_percentage == 25

    def test_saving_progress_percentage_complete(self, user, saving_factory):
        """Verifica porcentaje de progreso al 100%."""
        saving = saving_factory(
            user, target_amount=Decimal("10000.00"), current_amount=Decimal("10000.00")
        )

        assert saving.progress_percentage == 100

    def test_saving_progress_over_100(self, user, saving_factory):
        """Verifica porcentaje cuando se supera el objetivo."""
        saving = saving_factory(
            user, target_amount=Decimal("10000.00"), current_amount=Decimal("12000.00")
        )

        assert saving.progress_percentage >= 100

    def test_saving_remaining_amount(self, user, saving_factory):
        """Verifica monto restante."""
        saving = saving_factory(
            user, target_amount=Decimal("10000.00"), current_amount=Decimal("3000.00")
        )

        assert saving.remaining_amount == Decimal("7000.00")

    def test_saving_soft_delete(self, saving):
        """Verifica soft delete."""
        saving.soft_delete()

        assert saving.is_active is False

    def test_saving_timestamps(self, saving):
        """Verifica timestamps."""
        assert saving.created_at is not None
        assert saving.updated_at is not None


@pytest.mark.django_db
class TestSavingMethods:
    """Tests para los métodos de Saving."""

    def test_add_deposit(self, saving):
        """Verifica agregar depósito."""
        initial_amount = saving.current_amount
        deposit_amount = Decimal("1000.00")

        saving.add_deposit(deposit_amount)
        saving.refresh_from_db()

        assert saving.current_amount == initial_amount + deposit_amount

    def test_add_deposit_creates_movement(self, saving):
        """Verifica que add_deposit crea un movimiento."""
        saving.add_deposit(Decimal("500.00"))

        movements = SavingMovement.objects.filter(saving=saving)

        assert movements.count() >= 1
        assert movements.filter(type="DEPOSIT").exists()

    def test_add_withdrawal(self, saving_with_progress):
        """Verifica agregar retiro."""
        initial_amount = saving_with_progress.current_amount
        withdrawal_amount = Decimal("1000.00")

        saving_with_progress.add_withdrawal(withdrawal_amount)
        saving_with_progress.refresh_from_db()

        assert saving_with_progress.current_amount == initial_amount - withdrawal_amount

    def test_add_withdrawal_creates_movement(self, saving_with_progress):
        """Verifica que add_withdrawal crea un movimiento."""
        saving_with_progress.add_withdrawal(Decimal("500.00"))

        movements = SavingMovement.objects.filter(saving=saving_with_progress)

        assert movements.filter(type="WITHDRAWAL").exists()

    def test_withdrawal_cannot_exceed_balance(self, saving_with_progress):
        """Verifica que no se puede retirar más del saldo."""
        current = saving_with_progress.current_amount

        with pytest.raises(Exception):
            saving_with_progress.add_withdrawal(current + Decimal("1.00"))

    def test_deposit_completes_saving(self, user, saving_factory):
        """Verifica que depositar el monto restante completa la meta."""
        saving = saving_factory(
            user, target_amount=Decimal("10000.00"), current_amount=Decimal("9000.00")
        )

        saving.add_deposit(Decimal("1000.00"))
        saving.refresh_from_db()

        assert saving.status == SavingStatus.COMPLETED


@pytest.mark.django_db
class TestSavingMovementModel:
    """Tests para el modelo SavingMovement."""

    def test_create_deposit_movement(self, saving, saving_movement_factory):
        """Verifica creación de movimiento de depósito."""
        movement = saving_movement_factory(saving, "DEPOSIT", amount=Decimal("1000.00"))

        assert movement.pk is not None
        assert movement.type == "DEPOSIT"
        assert movement.amount == Decimal("1000.00")

    def test_create_withdrawal_movement(self, saving_with_progress, saving_movement_factory):
        """Verifica creación de movimiento de retiro."""
        movement = saving_movement_factory(
            saving_with_progress, "WITHDRAWAL", amount=Decimal("500.00")
        )

        assert movement.type == "WITHDRAWAL"

    def test_movement_str(self, saving, saving_movement_factory):
        """Verifica representación string del movimiento."""
        movement = saving_movement_factory(saving, "DEPOSIT")
        result = str(movement)

        assert "DEPOSIT" in result or str(movement.amount) in result

    def test_movement_belongs_to_saving(self, saving, saving_movement_factory):
        """Verifica relación con meta de ahorro."""
        movement = saving_movement_factory(saving, "DEPOSIT")

        assert movement.saving == saving

    def test_movement_has_date(self, saving, saving_movement_factory):
        """Verifica que el movimiento tiene fecha."""
        movement = saving_movement_factory(saving, "DEPOSIT")

        assert movement.date is not None


@pytest.mark.django_db
class TestSavingQuerySet:
    """Tests para el QuerySet de Saving."""

    def test_filter_active_savings(self, user, saving_factory):
        """Verifica filtro de metas activas."""
        active = saving_factory(user, name="Activa")
        completed = saving_factory(
            user,
            name="Completada",
            target_amount=Decimal("1000.00"),
            current_amount=Decimal("1000.00"),
        )
        completed.status = SavingStatus.COMPLETED
        completed.save()

        active_savings = Saving.objects.filter(user=user, status=SavingStatus.ACTIVE)

        assert active in active_savings
        assert completed not in active_savings

    def test_filter_by_user(self, user, other_user, saving_factory):
        """Verifica filtro por usuario."""
        saving_user1 = saving_factory(user, name="User 1 Saving")
        saving_user2 = saving_factory(other_user, name="User 2 Saving")

        user_savings = Saving.objects.filter(user=user)

        assert saving_user1 in user_savings
        assert saving_user2 not in user_savings


@pytest.mark.django_db
class TestSavingAutoComplete:
    """Tests para auto-completado de metas de ahorro."""

    def test_auto_complete_when_reaching_exact_target(self, user, saving_factory):
        """Verifica auto-complete al alcanzar exactamente la meta."""
        saving = saving_factory(
            user, target_amount=Decimal("10000.00"), current_amount=Decimal("9000.00")
        )

        # Asegurar que empieza como ACTIVE
        assert saving.status == SavingStatus.ACTIVE

        # Depositar justo lo que falta
        saving.add_deposit(Decimal("1000.00"))
        saving.refresh_from_db()

        # Debería auto-completarse
        assert saving.status == SavingStatus.COMPLETED
        assert saving.current_amount == saving.target_amount

    def test_auto_complete_when_exceeding_target(self, user, saving_factory):
        """Verifica auto-complete al superar la meta."""
        saving = saving_factory(
            user, target_amount=Decimal("10000.00"), current_amount=Decimal("9500.00")
        )

        # Depositar más de lo que falta
        saving.add_deposit(Decimal("1000.00"))
        saving.refresh_from_db()

        # Debería auto-completarse
        assert saving.status == SavingStatus.COMPLETED
        assert saving.current_amount > saving.target_amount

    def test_no_auto_complete_when_below_target(self, user, saving_factory):
        """Verifica que NO se auto-complete antes de alcanzar meta."""
        saving = saving_factory(
            user, target_amount=Decimal("10000.00"), current_amount=Decimal("5000.00")
        )

        # Depositar menos de lo que falta
        saving.add_deposit(Decimal("1000.00"))
        saving.refresh_from_db()

        # NO debería completarse
        assert saving.status == SavingStatus.ACTIVE
        assert saving.current_amount < saving.target_amount

    def test_remaining_amount_calculation(self, user, saving_factory):
        """Verifica cálculo de monto restante."""
        saving = saving_factory(
            user, target_amount=Decimal("10000.00"), current_amount=Decimal("3500.00")
        )

        assert saving.remaining_amount == Decimal("6500.00")

    def test_remaining_amount_zero_when_complete(self, user, saving_factory):
        """Verifica monto restante cero cuando está completa."""
        saving = saving_factory(
            user, target_amount=Decimal("10000.00"), current_amount=Decimal("10000.00")
        )

        assert saving.remaining_amount == Decimal("0.00")

    def test_remaining_amount_negative_when_exceeded(self, user, saving_factory):
        """Verifica monto restante negativo cuando se excede."""
        saving = saving_factory(
            user, target_amount=Decimal("10000.00"), current_amount=Decimal("12000.00")
        )

        # Puede ser negativo o cero según implementación
        assert saving.remaining_amount <= Decimal("0.00")
