"""Tests para las vistas de RecurringExpense."""

from django.urls import reverse

import pytest

from apps.recurring.models import RecurringExpense


@pytest.fixture
def recurring(user, expense_category):
    return RecurringExpense.objects.create(
        user=user,
        name="Edenor",
        category=expense_category,
        due_day=10,
    )


@pytest.mark.django_db
class TestRecurringListView:
    def test_login_required(self, client):
        response = client.get(reverse("recurring:list"))
        assert response.status_code == 302
        assert "login" in response.url

    def test_shows_user_recurrents(self, authenticated_client, recurring):
        response = authenticated_client.get(reverse("recurring:list"))
        assert response.status_code == 200
        assert "Edenor" in response.content.decode()

    def test_excludes_other_user_recurrents(
        self, authenticated_client, other_user, expense_category_factory
    ):
        other_cat = expense_category_factory(other_user, name="Otra")
        RecurringExpense.objects.create(
            user=other_user, name="Gasto Ajeno", category=other_cat, due_day=5
        )
        response = authenticated_client.get(reverse("recurring:list"))
        assert "Gasto Ajeno" not in response.content.decode()


@pytest.mark.django_db
class TestRecurringCreateView:
    def test_login_required(self, client):
        response = client.get(reverse("recurring:create"))
        assert response.status_code == 302

    def test_create_success(self, authenticated_client, user, expense_category):
        data = {
            "name": "AYSA",
            "category": expense_category.pk,
            "due_day": 15,
            "notes": "",
            "is_active": True,
        }
        response = authenticated_client.post(reverse("recurring:create"), data)
        assert response.status_code == 302
        assert RecurringExpense.objects.filter(name="AYSA", user=user).exists()

    def test_create_assigns_user(self, authenticated_client, user, expense_category):
        data = {"name": "Internet", "category": expense_category.pk, "due_day": 20, "notes": ""}
        authenticated_client.post(reverse("recurring:create"), data)
        rec = RecurringExpense.objects.get(name="Internet")
        assert rec.user == user

    def test_create_invalid_shows_error(self, authenticated_client, expense_category):
        data = {"name": "", "category": expense_category.pk, "due_day": 10}
        response = authenticated_client.post(reverse("recurring:create"), data)
        assert response.status_code == 200
        assert "form" in response.context

    def test_create_success_adds_toast(self, authenticated_client, user, expense_category):
        data = {"name": "Gas", "category": expense_category.pk, "due_day": 5, "notes": ""}
        response = authenticated_client.post(reverse("recurring:create"), data, follow=True)
        msgs = [m.message for m in response.context["messages"]]
        assert any("Gas" in m for m in msgs)

    def test_create_form_renders_is_active_checkbox(self, authenticated_client):
        response = authenticated_client.get(reverse("recurring:create"))
        assert response.status_code == 200
        assert 'name="is_active"' in response.content.decode()

    def test_create_is_active_when_checkbox_sent(
        self, authenticated_client, user, expense_category
    ):
        data = {
            "name": "Agua",
            "category": expense_category.pk,
            "due_day": 15,
            "notes": "",
            "is_active": True,
        }
        authenticated_client.post(reverse("recurring:create"), data)
        rec = RecurringExpense.objects.get(name="Agua", user=user)
        assert rec.is_active is True


@pytest.mark.django_db
class TestRecurringUpdateView:
    def test_login_required(self, client, recurring):
        response = client.get(reverse("recurring:update", kwargs={"pk": recurring.pk}))
        assert response.status_code == 302

    def test_update_success(self, authenticated_client, recurring, expense_category):
        data = {
            "name": "Edenor Actualizado",
            "category": expense_category.pk,
            "due_day": 12,
            "notes": "",
            "is_active": True,
        }
        response = authenticated_client.post(
            reverse("recurring:update", kwargs={"pk": recurring.pk}), data
        )
        assert response.status_code == 302
        recurring.refresh_from_db()
        assert recurring.name == "Edenor Actualizado"

    def test_cannot_update_other_user(
        self, authenticated_client, other_user, expense_category_factory
    ):
        other_cat = expense_category_factory(other_user, name="Otra")
        other_rec = RecurringExpense.objects.create(
            user=other_user, name="Ajeno", category=other_cat, due_day=1
        )
        response = authenticated_client.get(
            reverse("recurring:update", kwargs={"pk": other_rec.pk})
        )
        assert response.status_code in [403, 404]


@pytest.mark.django_db
class TestRecurringDeleteView:
    def test_login_required(self, client, recurring):
        response = client.post(reverse("recurring:delete", kwargs={"pk": recurring.pk}))
        assert response.status_code == 302

    def test_delete_success(self, authenticated_client, recurring):
        pk = recurring.pk
        response = authenticated_client.post(reverse("recurring:delete", kwargs={"pk": pk}))
        assert response.status_code == 302
        assert not RecurringExpense.objects.filter(pk=pk).exists()

    def test_delete_adds_toast(self, authenticated_client, recurring):
        name = recurring.name
        response = authenticated_client.post(
            reverse("recurring:delete", kwargs={"pk": recurring.pk}), follow=True
        )
        msgs = [m.message for m in response.context["messages"]]
        assert any(name in m for m in msgs)

    def test_cannot_delete_other_user(
        self, authenticated_client, other_user, expense_category_factory
    ):
        other_cat = expense_category_factory(other_user, name="Otra")
        other_rec = RecurringExpense.objects.create(
            user=other_user, name="Ajeno", category=other_cat, due_day=1
        )
        response = authenticated_client.post(
            reverse("recurring:delete", kwargs={"pk": other_rec.pk})
        )
        assert response.status_code in [403, 404]


@pytest.mark.django_db
class TestRecurringFormStartingInstallment:
    def test_create_with_starting_installment(self, authenticated_client, user, expense_category):
        data = {
            "name": "Tarjeta cuotas",
            "category": expense_category.pk,
            "due_day": 10,
            "notes": "",
            "is_active": True,
            "total_installments": 12,
            "starting_installment": 4,
            "start_date": "2026-04-01",
        }
        authenticated_client.post(reverse("recurring:create"), data)
        rec = RecurringExpense.objects.get(name="Tarjeta cuotas", user=user)
        assert rec.starting_installment == 4
        assert rec.installments_paid == 3

    def test_starting_installment_equal_to_total_is_invalid(
        self, authenticated_client, expense_category
    ):
        data = {
            "name": "Cuota mala",
            "category": expense_category.pk,
            "due_day": 10,
            "notes": "",
            "total_installments": 4,
            "starting_installment": 4,
            "start_date": "2026-04-01",
        }
        response = authenticated_client.post(reverse("recurring:create"), data)
        assert response.status_code == 200
        assert not RecurringExpense.objects.filter(name="Cuota mala").exists()

    def test_starting_installment_without_total_is_invalid(
        self, authenticated_client, expense_category
    ):
        data = {
            "name": "Cuota sin total",
            "category": expense_category.pk,
            "due_day": 10,
            "notes": "",
            "starting_installment": 4,
        }
        response = authenticated_client.post(reverse("recurring:create"), data)
        assert response.status_code == 200
        assert not RecurringExpense.objects.filter(name="Cuota sin total").exists()
