"""
Tests de integración para el flujo completo de metas de ahorro.
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.urls import reverse

from apps.savings.models import Saving, SavingMovement, SavingStatus
from apps.savings.forms import SavingForm


@pytest.mark.django_db
class TestSavingCreationFlow:
    """Tests del flujo completo de metas de ahorro."""

    def test_create_saving_and_verify_in_list(
        self, authenticated_client, user
    ):
        """Verifica que una meta creada aparezca en la lista."""
        # Obtener valores válidos del form
        temp_form = SavingForm()
        icon_choices = list(temp_form.fields['icon'].choices)
        color_choices = list(temp_form.fields['color'].choices)
        
        # 1. Crear meta
        create_url = reverse('savings:create')
        data = {
            'name': 'Viaje a Europa',
            'target_amount': '500000.00',
            'currency': 'ARS',
            'icon': icon_choices[0][0] if icon_choices else 'bi-piggy-bank',
            'color': color_choices[0][0] if color_choices else 'green',
        }
        
        response = authenticated_client.post(create_url, data)
        assert response.status_code == 302
        
        # 2. Verificar en DB
        saving = Saving.objects.get(name='Viaje a Europa')
        assert saving.user == user
        assert saving.target_amount == Decimal('500000.00')
        assert saving.current_amount == Decimal('0')
        assert saving.status == SavingStatus.ACTIVE
        
        # 3. Verificar en lista
        list_url = reverse('savings:list')
        response = authenticated_client.get(list_url)
        
        assert response.status_code == 200
        assert 'Viaje a Europa' in response.content.decode()


@pytest.mark.django_db
class TestSavingMovementsFlow:
    """Tests del flujo de movimientos de ahorro."""

    def test_deposit_increases_balance(
        self, authenticated_client, user, saving
    ):
        """Verifica que un depósito aumente el saldo."""
        initial_amount = saving.current_amount
        
        movement_url = reverse('savings:add_movement', kwargs={'pk': saving.pk})
        data = {
            'type': 'DEPOSIT',
            'amount': '10000.00',
        }
        
        response = authenticated_client.post(movement_url, data)
        assert response.status_code == 302
        
        saving.refresh_from_db()
        assert saving.current_amount == initial_amount + Decimal('10000.00')

    def test_multiple_deposits_accumulate(
        self, authenticated_client, user, saving
    ):
        """Verifica que múltiples depósitos se acumulen."""
        movement_url = reverse('savings:add_movement', kwargs={'pk': saving.pk})
        
        # Hacer 3 depósitos
        for i in range(3):
            data = {
                'type': 'DEPOSIT',
                'amount': '5000.00',
            }
            authenticated_client.post(movement_url, data)
        
        saving.refresh_from_db()
        assert saving.current_amount == Decimal('15000.00')
        
        # Verificar que se crearon los movimientos
        movements = SavingMovement.objects.filter(saving=saving)
        assert movements.count() == 3

    def test_withdrawal_decreases_balance(
        self, authenticated_client, user, saving_with_progress
    ):
        """Verifica que un retiro disminuya el saldo."""
        initial_amount = saving_with_progress.current_amount
        
        movement_url = reverse('savings:add_movement', kwargs={'pk': saving_with_progress.pk})
        data = {
            'type': 'WITHDRAWAL',
            'amount': '5000.00',
        }
        
        response = authenticated_client.post(movement_url, data)
        assert response.status_code == 302
        
        saving_with_progress.refresh_from_db()
        assert saving_with_progress.current_amount == initial_amount - Decimal('5000.00')

    def test_deposit_and_withdrawal_flow(
        self, authenticated_client, user, saving
    ):
        """Verifica flujo completo de depósitos y retiros."""
        movement_url = reverse('savings:add_movement', kwargs={'pk': saving.pk})
        
        # Depositar
        authenticated_client.post(movement_url, {
            'type': 'DEPOSIT',
            'amount': '20000.00',
        })
        
        saving.refresh_from_db()
        assert saving.current_amount == Decimal('20000.00')
        
        # Retirar
        authenticated_client.post(movement_url, {
            'type': 'WITHDRAWAL',
            'amount': '5000.00',
        })
        
        saving.refresh_from_db()
        assert saving.current_amount == Decimal('15000.00')
        
        # Depositar más
        authenticated_client.post(movement_url, {
            'type': 'DEPOSIT',
            'amount': '10000.00',
        })
        
        saving.refresh_from_db()
        assert saving.current_amount == Decimal('25000.00')


@pytest.mark.django_db
class TestSavingCompletionFlow:
    """Tests del flujo de completar metas de ahorro."""

    def test_saving_auto_completes_when_target_reached(
        self, authenticated_client, user, saving
    ):
        """Verifica que la meta se complete automáticamente."""
        # Configurar meta pequeña
        saving.target_amount = Decimal('10000.00')
        saving.save()
        
        movement_url = reverse('savings:add_movement', kwargs={'pk': saving.pk})
        
        # Depositar exactamente el objetivo
        authenticated_client.post(movement_url, {
            'type': 'DEPOSIT',
            'amount': '10000.00',
        })
        
        saving.refresh_from_db()
        assert saving.current_amount == Decimal('10000.00')
        assert saving.status == SavingStatus.COMPLETED
        assert saving.progress_percentage == 100

    def test_saving_completes_when_exceeding_target(
        self, authenticated_client, user, saving
    ):
        """Verifica que la meta se complete al exceder el objetivo."""
        saving.target_amount = Decimal('10000.00')
        saving.save()
        
        movement_url = reverse('savings:add_movement', kwargs={'pk': saving.pk})
        
        # Depositar más del objetivo
        authenticated_client.post(movement_url, {
            'type': 'DEPOSIT',
            'amount': '15000.00',
        })
        
        saving.refresh_from_db()
        assert saving.current_amount == Decimal('15000.00')
        assert saving.status == SavingStatus.COMPLETED

    def test_progress_percentage_calculation(
        self, authenticated_client, user, saving
    ):
        """Verifica cálculo de porcentaje de progreso."""
        saving.target_amount = Decimal('100000.00')
        saving.save()
        
        movement_url = reverse('savings:add_movement', kwargs={'pk': saving.pk})
        
        # 25%
        authenticated_client.post(movement_url, {
            'type': 'DEPOSIT',
            'amount': '25000.00',
        })
        
        saving.refresh_from_db()
        assert saving.progress_percentage == 25
        
        # 75%
        authenticated_client.post(movement_url, {
            'type': 'DEPOSIT',
            'amount': '50000.00',
        })
        
        saving.refresh_from_db()
        assert saving.progress_percentage == 75