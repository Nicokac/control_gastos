from datetime import date
from decimal import Decimal

from django.urls import reverse

import pytest

from apps.expenses.models import Expense
from apps.recurring.detection import find_recurring_suggestions
from apps.recurring.models import DismissedRecurringSuggestion, RecurringExpense

TODAY = date(2026, 11, 21)


def months_back(day: date, n: int) -> date:
    index = day.year * 12 + day.month - 1 - n
    return date(index // 12, index % 12 + 1, min(day.day, 28))


@pytest.fixture
def spend(user, expense_category):
    def _spend(day, amount="1000", description="Netflix", owner=None, **kwargs):
        return Expense.objects.create(
            user=owner or user,
            category=kwargs.pop("category", expense_category),
            date=day,
            description=description,
            amount=Decimal(amount),
            currency=kwargs.pop("currency", "ARS"),
            exchange_rate=kwargs.pop("exchange_rate", Decimal("1")),
            **kwargs,
        )

    return _spend


@pytest.fixture
def monthly(spend):
    """Un gasto por mes en los `months` meses que terminan `last` meses antes de `today`."""

    def _monthly(months=3, today=TODAY, last=0, amounts=None, **kwargs):
        amounts = amounts or ["1000"] * months
        return [
            spend(months_back(today, last + months - 1 - i), amount=amounts[i], **kwargs)
            for i in range(months)
        ]

    return _monthly


@pytest.mark.django_db
class TestDeteccion:
    def test_tres_meses_seguidos_con_montos_parecidos(self, user, monthly, expense_category):
        expenses = monthly(amounts=["1000", "1100", "1150"], description="NETFLIX.com")

        [suggestion] = find_recurring_suggestions(user, TODAY)

        assert suggestion.key == "netflix com"
        assert suggestion.name == "NETFLIX.com"
        assert suggestion.category == expense_category
        assert suggestion.due_day == 21
        assert suggestion.amount == Decimal("1150")
        assert suggestion.months == 3
        assert suggestion.expense_ids == [e.pk for e in expenses]

    def test_agrupa_descripciones_con_mayusculas_y_acentos_distintos(self, user, spend):
        spend(date(2026, 9, 5), description="Gimnasio Club")
        spend(date(2026, 10, 5), description="GIMNASIO  club")
        spend(date(2026, 11, 5), description="gimnásio club!")

        assert [s.key for s in find_recurring_suggestions(user, TODAY)] == ["gimnasio club"]

    def test_dos_meses_no_alcanzan(self, user, monthly):
        monthly(months=2)

        assert find_recurring_suggestions(user, TODAY) == []

    def test_puede_terminar_el_mes_anterior(self, user, monthly):
        monthly(last=1)

        assert len(find_recurring_suggestions(user, TODAY)) == 1

    def test_si_dejo_de_aparecer_hace_dos_meses_no_se_sugiere(self, user, monthly):
        monthly(last=2)

        assert find_recurring_suggestions(user, TODAY) == []

    def test_un_mes_salteado_corta_la_racha(self, user, spend):
        for day in (date(2026, 7, 1), date(2026, 8, 1), date(2026, 10, 1), date(2026, 11, 1)):
            spend(day)

        assert find_recurring_suggestions(user, TODAY) == []

    def test_dos_veces_en_un_mes_no_es_un_gasto_fijo(self, user, monthly, spend):
        monthly(description="Uber")
        spend(date(2026, 11, 3), description="Uber")

        assert find_recurring_suggestions(user, TODAY) == []

    def test_cuenta_solo_la_racha_final(self, user, spend):
        spend(date(2026, 6, 1))
        spend(date(2026, 8, 1))
        spend(date(2026, 9, 1))
        spend(date(2026, 10, 1))
        spend(date(2026, 11, 1))

        [suggestion] = find_recurring_suggestions(user, TODAY)
        assert suggestion.months == 4

    def test_monto_fuera_del_20_por_ciento_no_se_sugiere(self, user, monthly):
        monthly(amounts=["1000", "1000", "1300"])

        assert find_recurring_suggestions(user, TODAY) == []

    def test_monto_justo_en_el_20_por_ciento_se_sugiere(self, user, monthly):
        monthly(amounts=["1000", "1000", "1200"])

        assert len(find_recurring_suggestions(user, TODAY)) == 1

    def test_monedas_distintas_no_se_sugieren(self, user, monthly, spend):
        monthly(months=2, last=1)
        spend(date(2026, 11, 2), amount="1000", currency="USD", exchange_rate=Decimal("1000"))

        assert find_recurring_suggestions(user, TODAY) == []

    def test_cruza_el_cambio_de_anio(self, user, spend):
        spend(date(2026, 11, 10))
        spend(date(2026, 12, 10))
        spend(date(2027, 1, 10))

        assert find_recurring_suggestions(user, date(2027, 1, 15))[0].months == 3

    def test_ignora_gastos_fuera_de_la_ventana_de_6_meses(self, user, spend):
        for month in range(3, 6):
            spend(date(2026, month, 1))

        assert find_recurring_suggestions(user, TODAY) == []

    def test_ignora_descripciones_vacias_o_sin_palabras(self, user, monthly):
        monthly(description="")
        monthly(description="***")

        assert find_recurring_suggestions(user, TODAY) == []

    def test_ignora_aportes_a_metas_de_ahorro(self, user, monthly, saving):
        monthly(description="Ahorro vacaciones", saving=saving)

        assert find_recurring_suggestions(user, TODAY) == []

    def test_ignora_gastos_ya_vinculados_a_un_gasto_fijo(self, user, monthly, expense_category):
        recurring = RecurringExpense.objects.create(
            user=user, name="Servicio de streaming", category=expense_category, due_day=5
        )
        monthly(recurring=recurring)

        assert find_recurring_suggestions(user, TODAY) == []

    def test_ignora_si_ya_hay_un_gasto_fijo_con_ese_nombre(self, user, monthly, expense_category):
        RecurringExpense.objects.create(
            user=user, name="NETFLIX", category=expense_category, due_day=5, is_active=False
        )
        monthly()

        assert find_recurring_suggestions(user, TODAY) == []

    def test_ignora_las_descartadas(self, user, monthly):
        DismissedRecurringSuggestion.objects.create(user=user, key="netflix")
        monthly()

        assert find_recurring_suggestions(user, TODAY) == []

    def test_solo_mira_los_gastos_del_usuario(
        self, user, other_user, monthly, expense_category_factory
    ):
        monthly(owner=other_user, category=expense_category_factory(user=other_user))
        DismissedRecurringSuggestion.objects.create(user=other_user, key="spotify")
        monthly(description="Spotify")

        assert find_recurring_suggestions(user, TODAY)[0].key == "spotify"
        assert [s.key for s in find_recurring_suggestions(other_user, TODAY)] == ["netflix"]

    def test_ordena_por_cantidad_de_meses_y_despues_por_monto(self, user, monthly):
        monthly(description="Spotify", amounts=["500"] * 3)
        monthly(description="Netflix", amounts=["900"] * 3)
        monthly(description="Gimnasio", months=4)

        assert [s.key for s in find_recurring_suggestions(user, TODAY)] == [
            "gimnasio",
            "netflix",
            "spotify",
        ]

    def test_consultas_constantes(self, user, monthly, django_assert_max_num_queries):
        for name in ("Netflix", "Spotify", "Gimnasio", "Internet", "Celular"):
            monthly(description=name, months=5)

        with django_assert_max_num_queries(3):
            assert len(find_recurring_suggestions(user, TODAY)) == 5


@pytest.fixture
def current_monthly(monthly, today):
    def _current(**kwargs):
        return monthly(today=today, **kwargs)

    return _current


@pytest.mark.django_db
class TestBannerEnGastos:
    url = reverse("expenses:list")

    def test_muestra_la_sugerencia(self, authenticated_client, current_monthly):
        current_monthly()

        response = authenticated_client.get(self.url)

        assert response.context["recurring_suggestion"].key == "netflix"
        content = response.content.decode()
        assert "se repite todos los meses" in content
        assert reverse("recurring:create") + "?suggestion=netflix" in content

    def test_sin_gastos_repetidos_no_hay_banner(self, authenticated_client):
        response = authenticated_client.get(self.url)

        assert response.context["recurring_suggestion"] is None
        assert "se repite todos los meses" not in response.content.decode()


@pytest.mark.django_db
class TestDescartarSugerencia:
    url = reverse("recurring:dismiss_suggestion")

    def test_descartar_no_la_vuelve_a_mostrar(self, authenticated_client, user, current_monthly):
        current_monthly()

        response = authenticated_client.post(self.url, {"suggestion": "netflix"}, follow=True)

        assert response.redirect_chain[-1][0] == reverse("expenses:list")
        assert response.context["recurring_suggestion"] is None
        assert DismissedRecurringSuggestion.objects.filter(user=user, key="netflix").exists()
        messages = [str(m) for m in response.context["messages"]]
        assert "Listo, no te lo vamos a sugerir de nuevo." in messages

    def test_descartar_dos_veces_no_falla(self, authenticated_client, user):
        authenticated_client.post(self.url, {"suggestion": "netflix"})
        authenticated_client.post(self.url, {"suggestion": "netflix"})

        assert DismissedRecurringSuggestion.objects.filter(user=user).count() == 1

    def test_requiere_login(self, client):
        response = client.post(self.url, {"suggestion": "netflix"})

        assert response.status_code == 302
        assert not DismissedRecurringSuggestion.objects.exists()

    def test_get_no_permitido(self, authenticated_client):
        assert authenticated_client.get(self.url).status_code == 405


@pytest.mark.django_db
class TestCrearDesdeSugerencia:
    url = reverse("recurring:create")

    def test_precarga_el_formulario(self, authenticated_client, current_monthly, expense_category):
        expenses = current_monthly(amounts=["1000", "1000", "1100"])

        response = authenticated_client.get(self.url, {"suggestion": "netflix"})

        form = response.context["form"]
        assert form.initial["name"] == "Netflix"
        assert form.initial["category"] == expense_category
        assert form.initial["due_day"] == expenses[-1].date.day
        assert form.initial["estimated_amount"] == Decimal("1100")
        content = response.content.decode()
        assert 'name="suggestion" value="netflix"' in content
        assert "los 3 pagos detectados quedan vinculados" in content

    def test_al_guardar_vincula_los_gastos_detectados(
        self, authenticated_client, user, current_monthly, spend, expense_category, today
    ):
        expenses = current_monthly()
        other = spend(today, description="Supermercado")

        response = authenticated_client.post(
            self.url,
            {
                "suggestion": "netflix",
                "name": "Netflix",
                "category": expense_category.pk,
                "due_day": 5,
                "is_active": "on",
            },
            follow=True,
        )

        recurring = RecurringExpense.objects.get(user=user)
        assert sorted(recurring.expenses.values_list("pk", flat=True)) == [e.pk for e in expenses]
        assert recurring.is_paid_in(today.month, today.year)
        other.refresh_from_db()
        assert other.recurring is None
        messages = [str(m) for m in response.context["messages"]]
        assert any("3 pagos quedaron vinculados" in m for m in messages)
        assert find_recurring_suggestions(user) == []

    def test_sugerencia_inexistente_crea_sin_vincular(
        self, authenticated_client, user, current_monthly, expense_category
    ):
        current_monthly()

        authenticated_client.post(
            self.url,
            {
                "suggestion": "otra cosa",
                "name": "Otra cosa",
                "category": expense_category.pk,
                "due_day": 5,
                "is_active": "on",
            },
        )

        assert RecurringExpense.objects.get(user=user).expenses.count() == 0

    def test_no_puede_vincular_gastos_de_otro_usuario(
        self,
        authenticated_client,
        user,
        other_user,
        current_monthly,
        expense_category,
        expense_category_factory,
    ):
        current_monthly(owner=other_user, category=expense_category_factory(user=other_user))

        response = authenticated_client.get(self.url, {"suggestion": "netflix"})
        assert response.context["suggestion"] is None

        authenticated_client.post(
            self.url,
            {
                "suggestion": "netflix",
                "name": "Netflix",
                "category": expense_category.pk,
                "due_day": 5,
                "is_active": "on",
            },
        )
        assert RecurringExpense.objects.get(user=user).expenses.count() == 0
        assert not Expense.objects.filter(user=other_user, recurring__isnull=False).exists()
