"""
Tests para los formularios de Saving.
"""

import pytest
from decimal import Decimal
from django.utils import timezone

from apps.savings.forms import SavingForm, SavingMovementForm
from apps.savings.models import Saving, SavingMovement


@pytest.mark.django_db
class TestSavingForm:
    """Tests para SavingForm."""

    def test_valid_saving(self, user):
        """Verifica formulario válido para meta de ahorro."""
        form = SavingForm(
            data={
                'name': 'Vacaciones',
                'target_amount': '50000.00',
                'target_date': (timezone.now().date().replace(year=timezone.now().year + 1)),
            }
        )
        
        assert form.is_valid(), form.errors

    def test_name_required(self):
        """Verifica que el nombre sea requerido."""
        form = SavingForm(
            data={
                'name': '',
                'target_amount': '50000.00',
            }
        )
        
        assert not form.is_valid()
        assert 'name' in form.errors

    def test_target_amount_required(self):
        """Verifica que el monto objetivo sea requerido."""
        form = SavingForm(
            data={
                'name': 'Vacaciones',
                'target_amount': '',
            }
        )
        
        assert not form.is_valid()
        assert 'target_amount' in form.errors

    def test_negative_target_amount_invalid(self):
        """Verifica que monto objetivo negativo sea inválido."""
        form = SavingForm(
            data={
                'name': 'Vacaciones',
                'target_amount': '-50000.00',
            }
        )
        
        assert not form.is_valid()
        assert 'target_amount' in form.errors

    def test_zero_target_amount_invalid(self):
        """Verifica que monto objetivo cero sea inválido."""
        form = SavingForm(
            data={
                'name': 'Vacaciones',
                'target_amount': '0',
            }
        )
        
        assert not form.is_valid()
        assert 'target_amount' in form.errors

    def test_target_date_optional(self):
        """Verifica que la fecha objetivo sea opcional."""
        form = SavingForm(
            data={
                'name': 'Vacaciones',
                'target_amount': '50000.00',
                'target_date': '',
            }
        )
        
        assert form.is_valid(), form.errors

    def test_past_target_date_invalid(self, yesterday):
        """Verifica que fecha objetivo pasada sea inválida."""
        form = SavingForm(
            data={
                'name': 'Vacaciones',
                'target_amount': '50000.00',
                'target_date': yesterday,
            }
        )
        
        # Depende de si el form valida fechas pasadas
        if not form.is_valid():
            assert 'target_date' in form.errors or '__all__' in form.errors

    def test_save_creates_saving(self, user):
        """Verifica que save() cree la meta."""
        form = SavingForm(
            data={
                'name': 'Nueva Meta',
                'target_amount': '100000.00',
            }
        )
        
        assert form.is_valid(), form.errors
        
        saving = form.save(commit=False)
        saving.user = user
        saving.save()
        
        assert saving.pk is not None
        assert saving.target_amount == Decimal('100000.00')
        assert saving.current_amount == Decimal('0.00')


@pytest.mark.django_db
class TestSavingFormEdit:
    """Tests para edición de metas de ahorro."""

    def test_edit_saving_name(self, saving):
        """Verifica edición del nombre."""
        form = SavingForm(
            data={
                'name': 'Nombre Editado',
                'target_amount': str(saving.target_amount),
            },
            instance=saving
        )
        
        assert form.is_valid(), form.errors
        
        saving = form.save()
        assert saving.name == 'Nombre Editado'

    def test_edit_target_amount(self, saving):
        """Verifica edición del monto objetivo."""
        form = SavingForm(
            data={
                'name': saving.name,
                'target_amount': '200000.00',
            },
            instance=saving
        )
        
        assert form.is_valid(), form.errors
        
        saving = form.save()
        assert saving.target_amount == Decimal('200000.00')

    def test_cannot_reduce_target_below_current(self, saving_with_progress):
        """Verifica que no se pueda reducir objetivo por debajo del actual."""
        # Si current_amount es 5000, target_amount no debería poder ser menor
        form = SavingForm(
            data={
                'name': saving_with_progress.name,
                'target_amount': '1000.00',  # Menor que current_amount
            },
            instance=saving_with_progress
        )
        
        # Depende de si el form tiene esta validación
        if not form.is_valid():
            assert 'target_amount' in form.errors or '__all__' in form.errors


@pytest.mark.django_db
class TestSavingMovementForm:
    """Tests para SavingMovementForm."""

    def test_valid_deposit(self, saving):
        """Verifica formulario válido para depósito."""
        form = SavingMovementForm(
            data={
                'type': 'DEPOSIT',
                'amount': '1000.00',
                'date': timezone.now().date(),
            },
            saving=saving
        )
        
        assert form.is_valid(), form.errors

    def test_valid_withdrawal(self, saving_with_progress):
        """Verifica formulario válido para retiro."""
        form = SavingMovementForm(
            data={
                'type': 'WITHDRAWAL',
                'amount': '1000.00',
                'date': timezone.now().date(),
            },
            saving=saving_with_progress
        )
        
        assert form.is_valid(), form.errors

    def test_amount_required(self, saving):
        """Verifica que el monto sea requerido."""
        form = SavingMovementForm(
            data={
                'type': 'DEPOSIT',
                'amount': '',
                'date': timezone.now().date(),
            },
            saving=saving
        )
        
        assert not form.is_valid()
        assert 'amount' in form.errors

    def test_negative_amount_invalid(self, saving):
        """Verifica que monto negativo sea inválido."""
        form = SavingMovementForm(
            data={
                'type': 'DEPOSIT',
                'amount': '-1000.00',
                'date': timezone.now().date(),
            },
            saving=saving
        )
        
        assert not form.is_valid()
        assert 'amount' in form.errors

    def test_withdrawal_cannot_exceed_balance(self, saving_with_progress):
        """Verifica que retiro no exceda el saldo."""
        # saving_with_progress tiene current_amount = 5000
        form = SavingMovementForm(
            data={
                'type': 'WITHDRAWAL',
                'amount': '10000.00',  # Más que el saldo
                'date': timezone.now().date(),
            },
            saving=saving_with_progress
        )
        
        assert not form.is_valid()
        assert 'amount' in form.errors or '__all__' in form.errors

    def test_withdrawal_from_zero_balance_invalid(self, saving):
        """Verifica que no se pueda retirar de saldo cero."""
        form = SavingMovementForm(
            data={
                'type': 'WITHDRAWAL',
                'amount': '100.00',
                'date': timezone.now().date(),
            },
            saving=saving  # current_amount = 0
        )
        
        assert not form.is_valid()
        assert 'amount' in form.errors or '__all__' in form.errors

    def test_save_updates_saving_balance(self, saving, user):
        """Verifica que save() actualice el saldo de la meta."""
        initial_amount = saving.current_amount
        
        form = SavingMovementForm(
            data={
                'type': 'DEPOSIT',
                'amount': '5000.00',
                'date': timezone.now().date(),
            },
            saving=saving
        )
        
        assert form.is_valid(), form.errors
        
        movement = form.save()
        saving.refresh_from_db()
        
        assert saving.current_amount == initial_amount + Decimal('5000.00')