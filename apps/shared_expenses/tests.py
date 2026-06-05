"""Tests para vistas y formularios de gastos compartidos."""

from datetime import date
from decimal import Decimal

from django.urls import reverse

import pytest

from apps.shared_expenses.models import HouseholdMember, SharedExpense


@pytest.fixture
def member(user):
    return HouseholdMember.objects.create(user=user, name="Pedro")


@pytest.fixture
def shared_expense(user, expense_category, member):
    return SharedExpense.objects.create(
        user=user,
        date=date(2026, 6, 1),
        description="Supermercado",
        amount=Decimal("5000"),
        currency="ARS",
        category=expense_category,
        paid_by=member,
    )


# =============================================================================
# HouseholdMemberForm
# =============================================================================


@pytest.mark.django_db
class TestHouseholdMemberForm:
    def test_valid_form(self, user):
        from apps.shared_expenses.forms import HouseholdMemberForm

        form = HouseholdMemberForm(data={"name": "Juan"}, user=user)
        assert form.is_valid()

    def test_duplicate_name_rejected(self, user, member):
        from apps.shared_expenses.forms import HouseholdMemberForm

        form = HouseholdMemberForm(data={"name": "Pedro"}, user=user)
        assert not form.is_valid()
        assert "name" in form.errors

    def test_duplicate_name_case_insensitive(self, user, member):
        from apps.shared_expenses.forms import HouseholdMemberForm

        form = HouseholdMemberForm(data={"name": "pedro"}, user=user)
        assert not form.is_valid()

    def test_edit_same_name_allowed(self, user, member):
        from apps.shared_expenses.forms import HouseholdMemberForm

        form = HouseholdMemberForm(data={"name": "Pedro"}, user=user, instance=member)
        assert form.is_valid()

    def test_save_assigns_user(self, user):
        from apps.shared_expenses.forms import HouseholdMemberForm

        form = HouseholdMemberForm(data={"name": "Pedro"}, user=user)
        assert form.is_valid()
        obj = form.save()
        assert obj.user == user


# =============================================================================
# SharedExpenseForm
# =============================================================================


@pytest.mark.django_db
class TestSharedExpenseForm:
    def _base_data(self, expense_category, member=None):
        data = {
            "date": "2026-06-01",
            "description": "Luz",
            "amount": "3000",
            "currency": "ARS",
            "exchange_rate": "1.0000",
            "category": expense_category.pk,
        }
        if member:
            data["paid_by"] = member.pk
        return data

    def test_valid_form(self, user, expense_category):
        from apps.shared_expenses.forms import SharedExpenseForm

        form = SharedExpenseForm(data=self._base_data(expense_category), user=user)
        assert form.is_valid(), form.errors

    def test_valid_with_member(self, user, expense_category, member):
        from apps.shared_expenses.forms import SharedExpenseForm

        form = SharedExpenseForm(data=self._base_data(expense_category, member), user=user)
        assert form.is_valid(), form.errors

    def test_categoria_ajena_rechazada(self, user, other_user, expense_category_factory):
        from apps.shared_expenses.forms import SharedExpenseForm

        other_cat = expense_category_factory(other_user, name="Ajena")
        data = {
            "date": "2026-06-01",
            "description": "Test",
            "amount": "1000",
            "currency": "ARS",
            "exchange_rate": "1.0000",
            "category": other_cat.pk,
        }
        form = SharedExpenseForm(data=data, user=user)
        assert not form.is_valid()
        assert "category" in form.errors

    def test_miembro_ajeno_rechazado(self, user, other_user, expense_category):
        from apps.shared_expenses.forms import SharedExpenseForm

        other_member = HouseholdMember.objects.create(user=other_user, name="Ajeno")
        data = self._base_data(expense_category, other_member)
        form = SharedExpenseForm(data=data, user=user)
        assert not form.is_valid()
        assert "paid_by" in form.errors

    def test_save_assigns_user(self, user, expense_category):
        from apps.shared_expenses.forms import SharedExpenseForm

        form = SharedExpenseForm(data=self._base_data(expense_category), user=user)
        assert form.is_valid()
        obj = form.save()
        assert obj.user == user


# =============================================================================
# Vistas — SharedExpense
# =============================================================================


@pytest.mark.django_db
class TestSharedExpenseListView:
    url = reverse("shared_expenses:list")

    def test_login_required(self, client):
        response = client.get(self.url)
        assert response.status_code == 302
        assert "login" in response.url

    def test_lista_propios(self, authenticated_client, shared_expense):
        response = authenticated_client.get(self.url)
        assert response.status_code == 200
        assert "Supermercado" in response.content.decode()

    def test_no_muestra_ajenos(self, authenticated_client, other_user, expense_category_factory):
        other_cat = expense_category_factory(other_user, name="Otra")
        SharedExpense.objects.create(
            user=other_user,
            date=date(2026, 6, 1),
            description="Gasto ajeno",
            amount=Decimal("1000"),
            currency="ARS",
            category=other_cat,
        )
        response = authenticated_client.get(self.url)
        assert "Gasto ajeno" not in response.content.decode()

    def test_filtro_por_mes(self, authenticated_client, shared_expense, expense_category, user):
        SharedExpense.objects.create(
            user=user,
            date=date(2026, 5, 1),
            description="Mayo gasto",
            amount=Decimal("1000"),
            currency="ARS",
            category=expense_category,
        )
        response = authenticated_client.get(self.url + "?month=6&year=2026")
        content = response.content.decode()
        assert "Supermercado" in content
        assert "Mayo gasto" not in content


@pytest.mark.django_db
class TestSharedExpenseCreateView:
    url = reverse("shared_expenses:create")

    def test_login_required(self, client):
        assert client.get(self.url).status_code == 302

    def test_crear_gasto(self, authenticated_client, user, expense_category):
        data = {
            "date": "2026-06-01",
            "description": "Agua",
            "amount": "2000",
            "currency": "ARS",
            "exchange_rate": "1.0000",
            "category": expense_category.pk,
        }
        response = authenticated_client.post(self.url, data)
        assert response.status_code == 302
        assert SharedExpense.objects.filter(description="Agua", user=user).exists()

    def test_form_invalido_muestra_error(self, authenticated_client, expense_category):
        data = {
            "date": "",
            "description": "",
            "amount": "",
            "currency": "ARS",
            "category": expense_category.pk,
        }
        response = authenticated_client.post(self.url, data)
        assert response.status_code == 200


@pytest.mark.django_db
class TestSharedExpenseUpdateView:
    def test_login_required(self, client, shared_expense):
        url = reverse("shared_expenses:update", kwargs={"pk": shared_expense.pk})
        assert client.get(url).status_code == 302

    def test_actualizar_gasto(self, authenticated_client, shared_expense, expense_category):
        url = reverse("shared_expenses:update", kwargs={"pk": shared_expense.pk})
        data = {
            "date": "2026-06-01",
            "description": "Supermercado actualizado",
            "amount": "6000",
            "currency": "ARS",
            "exchange_rate": "1.0000",
            "category": expense_category.pk,
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == 302
        shared_expense.refresh_from_db()
        assert shared_expense.description == "Supermercado actualizado"

    def test_no_puede_editar_ajeno(
        self, authenticated_client, other_user, expense_category_factory
    ):
        other_cat = expense_category_factory(other_user, name="Otra")
        other_exp = SharedExpense.objects.create(
            user=other_user,
            date=date(2026, 6, 1),
            description="Ajeno",
            amount=Decimal("1000"),
            currency="ARS",
            category=other_cat,
        )
        url = reverse("shared_expenses:update", kwargs={"pk": other_exp.pk})
        assert authenticated_client.get(url).status_code in [403, 404]


@pytest.mark.django_db
class TestSharedExpenseDeleteView:
    def test_eliminar_gasto(self, authenticated_client, shared_expense):
        pk = shared_expense.pk
        url = reverse("shared_expenses:delete", kwargs={"pk": pk})
        response = authenticated_client.post(url)
        assert response.status_code == 302
        assert not SharedExpense.objects.filter(pk=pk).exists()

    def test_no_puede_eliminar_ajeno(
        self, authenticated_client, other_user, expense_category_factory
    ):
        other_cat = expense_category_factory(other_user, name="Otra")
        other_exp = SharedExpense.objects.create(
            user=other_user,
            date=date(2026, 6, 1),
            description="Ajeno",
            amount=Decimal("1000"),
            currency="ARS",
            category=other_cat,
        )
        url = reverse("shared_expenses:delete", kwargs={"pk": other_exp.pk})
        assert authenticated_client.post(url).status_code in [403, 404]


# =============================================================================
# Vistas — HouseholdMember
# =============================================================================


@pytest.mark.django_db
class TestHouseholdMemberViews:
    def test_lista_miembros(self, authenticated_client, member):
        response = authenticated_client.get(reverse("shared_expenses:members"))
        assert response.status_code == 200
        assert "Pedro" in response.content.decode()

    def test_crear_miembro(self, authenticated_client, user):
        response = authenticated_client.post(
            reverse("shared_expenses:member_create"), {"name": "Carlos"}
        )
        assert response.status_code == 302
        assert HouseholdMember.objects.filter(name="Carlos", user=user).exists()

    def test_eliminar_miembro(self, authenticated_client, member):
        pk = member.pk
        url = reverse("shared_expenses:member_delete", kwargs={"pk": pk})
        response = authenticated_client.post(url)
        assert response.status_code == 302
        assert not HouseholdMember.objects.filter(pk=pk).exists()

    def test_no_puede_eliminar_miembro_ajeno(self, authenticated_client, other_user):
        other_member = HouseholdMember.objects.create(user=other_user, name="Ajeno")
        url = reverse("shared_expenses:member_delete", kwargs={"pk": other_member.pk})
        assert authenticated_client.post(url).status_code in [403, 404]


# =============================================================================
# Export
# =============================================================================


@pytest.mark.django_db
class TestSharedExpenseExportView:
    def test_export_devuelve_xlsx(self, authenticated_client, shared_expense):
        response = authenticated_client.get(
            reverse("shared_expenses:export") + "?month=6&year=2026"
        )
        assert response.status_code == 200
        assert "spreadsheetml" in response["Content-Type"]

    def test_export_sin_datos(self, authenticated_client):
        response = authenticated_client.get(
            reverse("shared_expenses:export") + "?month=1&year=2020"
        )
        assert response.status_code == 200
