"""Selector de fecha en español en los formularios web (DT-109)."""

import datetime
import re

from django.urls import reverse

import pytest

from apps.recurring.models import RecurringExpense

FORM_URLS = [
    "expenses:create",
    "income:create",
    "recurring:create",
    "savings:create",
    "shared_expenses:create",
]


@pytest.mark.django_db
class TestDatePickerAssets:
    @pytest.mark.parametrize("url_name", FORM_URLS)
    def test_form_loads_spanish_date_picker(self, authenticated_client, url_name):
        response = authenticated_client.get(reverse(url_name))
        html = response.content.decode()

        assert response.status_code == 200
        assert 'type="date"' in html
        assert "flatpickr@4.6.13/dist/flatpickr.min.js" in html
        assert "flatpickr@4.6.13/dist/l10n/es.js" in html
        assert "js/date_picker.js?v=" in html


@pytest.mark.django_db
class TestDateInputValueFormat:
    def test_recurring_start_date_renders_iso(self, authenticated_client, user, expense_category):
        rec = RecurringExpense.objects.create(
            user=user,
            name="Tarjeta cuotas",
            category=expense_category,
            due_day=10,
            total_installments=12,
            start_date=datetime.date(2026, 4, 1),
        )

        response = authenticated_client.get(reverse("recurring:update", kwargs={"pk": rec.pk}))
        tag = re.search(r'<input[^>]*name="start_date"[^>]*>', response.content.decode()).group()

        assert 'value="2026-04-01"' in tag

    def test_expense_date_renders_iso(self, authenticated_client):
        response = authenticated_client.get(reverse("expenses:create"))
        tag = re.search(r'<input[^>]*name="date"[^>]*>', response.content.decode()).group()

        assert re.search(r'value="\d{4}-\d{2}-\d{2}"', tag)
