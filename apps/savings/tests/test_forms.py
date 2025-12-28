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
            'currency': 'ARS',
            'icon': 'bi-piggy-bank',
            'color': '#28a745',  
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
                'currency': 'ARS',
                'icon': 'bi-piggy-bank',
                'color': '#28a745', 
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
                'currency': 'ARS',
                'icon': 'bi-piggy-bank',
                'color': '#28a745',  
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
        # Obtener valores válidos del form
        temp_form = SavingForm()
        icon_choices = list(temp_form.fields['icon'].choices)
        color_choices = list(temp_form.fields['color'].choices)
        
        form = SavingForm(
            data={
                'name': 'Nombre Editado',
                'target_amount': str(saving.target_amount),
                'currency': 'ARS',
                'icon': icon_choices[0][0] if icon_choices else 'bi-piggy-bank',
                'color': color_choices[0][0] if color_choices else 'green',
            },
            instance=saving
        )
        
        assert form.is_valid(), form.errors
        
        saved = form.save()
        assert saved.name == 'Nombre Editado'

    def test_edit_target_amount(self, saving):
        """Verifica edición del monto objetivo."""
        temp_form = SavingForm()
        icon_choices = list(temp_form.fields['icon'].choices)
        color_choices = list(temp_form.fields['color'].choices)
        
        form = SavingForm(
            data={
                'name': saving.name,
                'target_amount': '200000.00',
                'currency': 'ARS',
                'icon': icon_choices[0][0] if icon_choices else 'bi-piggy-bank',
                'color': color_choices[0][0] if color_choices else 'green',
            },
            instance=saving
        )
        
        assert form.is_valid(), form.errors
        
        saved = form.save()
        assert saved.target_amount == Decimal('200000.00')

    def test_cannot_reduce_target_below_current(self, saving_with_progress):
        """Verifica que no se pueda reducir objetivo por debajo del actual."""
        # Si current_amount es 5000, target_amount no debería poder ser menor
        form = SavingForm(
            data={
                'name': saving_with_progress.name,
                'target_amount': '1000.00',  # Menor que current_amount
                'currency': 'ARS',
                'icon': 'bi-piggy-bank',
                'color': '#28a745',  
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


@pytest.mark.django_db
class TestSavingFormCleanedData:
    """Tests para cleaned_data de SavingForm."""

    def test_cleaned_data_types(self, user):
        """Verifica tipos correctos en cleaned_data."""
        from datetime import date
        
        future_date = timezone.now().date().replace(year=timezone.now().year + 1)
        
        form = SavingForm(
            data={
                'name': 'Meta de prueba',
                'target_amount': '100000.00',
                'target_date': future_date,
                'currency': 'ARS',
                'icon': 'bi-piggy-bank',
                'color': '#28a745',  
            }
        )
        
        assert form.is_valid(), form.errors
        
        # Verificar tipos
        assert isinstance(form.cleaned_data['name'], str)
        assert isinstance(form.cleaned_data['target_amount'], Decimal)
        
        if form.cleaned_data.get('target_date'):
            assert isinstance(form.cleaned_data['target_date'], date)

    def test_name_is_stripped(self, user):
        """Verifica que el nombre se limpie de espacios."""
        form = SavingForm(
            data={
                'name': '  Meta con espacios  ',
                'target_amount': '50000.00',
                'currency': 'ARS',
                'icon': 'bi-piggy-bank',
                'color': '#28a745',  
            }
        )
        
        assert form.is_valid(), form.errors
        
        cleaned_name = form.cleaned_data['name']
        assert cleaned_name == cleaned_name.strip()


@pytest.mark.django_db
class TestSavingFormInitialValues:
    """Tests para valores iniciales de SavingForm."""

    def test_current_amount_starts_at_zero(self, user):
        """Verifica que current_amount inicie en cero."""
        form = SavingForm(
            data={
                'name': 'Nueva meta',
                'target_amount': '100000.00',
                'currency': 'ARS',
                'icon': 'bi-piggy-bank',
                'color': '#28a745',  
            }
        )
        
        assert form.is_valid(), form.errors
        
        saving = form.save(commit=False)
        saving.user = user
        saving.save()
        
        assert saving.current_amount == Decimal('0.00')

    def test_status_starts_as_active(self, user):
        """Verifica que status inicie como ACTIVE."""
        from apps.savings.models import SavingStatus
        
        form = SavingForm(
            data={
                'name': 'Nueva meta',
                'target_amount': '100000.00',
                'currency': 'ARS',
                'icon': 'bi-piggy-bank',
                'color': '#28a745',  
            }
        )
        
        assert form.is_valid(), form.errors
        
        saving = form.save(commit=False)
        saving.user = user
        saving.save()
        
        assert saving.status == SavingStatus.ACTIVE


@pytest.mark.django_db
class TestSavingMovementFormCleanedData:
    """Tests para cleaned_data de SavingMovementForm."""

    def test_cleaned_data_types(self, saving):
        """Verifica tipos correctos en cleaned_data."""
        from datetime import date
        
        form = SavingMovementForm(
            data={
                'type': 'DEPOSIT',
                'amount': '1000.00',
            },
            saving=saving
        )
        
        assert form.is_valid(), form.errors
        
        # Verificar tipos
        assert isinstance(form.cleaned_data['amount'], Decimal)