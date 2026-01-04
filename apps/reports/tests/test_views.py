"""
Tests para las vistas de reportes y dashboard.
"""

from decimal import Decimal

from django.urls import reverse
from django.utils import timezone

import pytest

from apps.categories.models import Category, CategoryType
from apps.expenses.models import Expense
from apps.income.models import Income


@pytest.mark.django_db
class TestDashboardView:
    """Tests para la vista del dashboard."""

    def test_dashboard_requires_login(self, client):
        """Verifica que el dashboard requiere autenticación."""
        response = client.get(reverse("reports:dashboard"))
        assert response.status_code == 302
        assert "/users/login/" in response.url

    def test_dashboard_renders_for_authenticated_user(self, client, user):
        """Verifica que el dashboard renderiza para usuarios autenticados."""
        client.force_login(user)
        response = client.get(reverse("reports:dashboard"))
        assert response.status_code == 200
        assert "reports/dashboard.html" in [t.name for t in response.templates]

    def test_dashboard_empty_state(self, client, user):
        """Verifica el estado vacío del dashboard."""
        client.force_login(user)
        response = client.get(reverse("reports:dashboard"))
        assert response.status_code == 200
        assert response.context["income_total"] == Decimal("0")
        assert response.context["expense_total"] == Decimal("0")

    def test_dashboard_shows_balance(self, client, user):
        """Verifica que el dashboard muestra el balance correctamente."""
        client.force_login(user)

        # Crear categorías
        income_cat = Category.objects.create(
            name="Salario Test",
            type=CategoryType.INCOME,
            is_system=True,
        )
        expense_cat = Category.objects.create(
            name="Comida Test",
            type=CategoryType.EXPENSE,
            is_system=True,
        )

        today = timezone.now().date()

        # Crear ingreso
        Income.objects.create(
            user=user,
            category=income_cat,
            description="Sueldo",
            amount=Decimal("1000.00"),
            amount_ars=Decimal("1000.00"),
            currency="ARS",
            exchange_rate=Decimal("1.00"),
            date=today,
        )

        # Crear gasto
        Expense.objects.create(
            user=user,
            category=expense_cat,
            description="Almuerzo",
            amount=Decimal("200.00"),
            amount_ars=Decimal("200.00"),
            currency="ARS",
            exchange_rate=Decimal("1.00"),
            date=today,
        )

        response = client.get(reverse("reports:dashboard"))
        assert response.status_code == 200
        assert response.context["income_total"] == Decimal("1000.00")
        assert response.context["expense_total"] == Decimal("200.00")
        assert response.context["balance"] == Decimal("800.00")
        assert response.context["balance_is_positive"] is True

    def test_dashboard_negative_balance(self, client, user):
        """Verifica el dashboard con balance negativo."""
        client.force_login(user)

        income_cat = Category.objects.create(
            name="Salario Test",
            type=CategoryType.INCOME,
            is_system=True,
        )
        expense_cat = Category.objects.create(
            name="Comida Test",
            type=CategoryType.EXPENSE,
            is_system=True,
        )

        today = timezone.now().date()

        Income.objects.create(
            user=user,
            category=income_cat,
            description="Sueldo",
            amount=Decimal("500.00"),
            amount_ars=Decimal("500.00"),
            currency="ARS",
            exchange_rate=Decimal("1.00"),
            date=today,
        )

        Expense.objects.create(
            user=user,
            category=expense_cat,
            description="Gasto grande",
            amount=Decimal("800.00"),
            amount_ars=Decimal("800.00"),
            currency="ARS",
            exchange_rate=Decimal("1.00"),
            date=today,
        )

        response = client.get(reverse("reports:dashboard"))
        assert response.context["balance"] == Decimal("-300.00")
        assert response.context["balance_is_positive"] is False


@pytest.mark.django_db
class TestRecentTransactions:
    """Tests para las transacciones recientes del dashboard."""

    def test_recent_transactions_empty(self, client, user):
        """Verifica que sin transacciones la lista está vacía."""
        client.force_login(user)
        response = client.get(reverse("reports:dashboard"))
        assert response.context["recent_transactions"] == []

    def test_recent_transactions_shows_expenses(self, client, user):
        """Verifica que los gastos aparecen en transacciones recientes."""
        client.force_login(user)

        expense_cat = Category.objects.create(
            name="Test Cat",
            type=CategoryType.EXPENSE,
            is_system=True,
        )

        today = timezone.now().date()

        Expense.objects.create(
            user=user,
            category=expense_cat,
            description="Gasto Test",
            amount=Decimal("100.00"),
            amount_ars=Decimal("100.00"),
            currency="ARS",
            exchange_rate=Decimal("1.00"),
            date=today,
        )

        response = client.get(reverse("reports:dashboard"))
        transactions = response.context["recent_transactions"]
        assert len(transactions) == 1
        assert transactions[0]["type"] == "expense"
        assert transactions[0]["description"] == "Gasto Test"

    def test_recent_transactions_shows_incomes(self, client, user):
        """Verifica que los ingresos aparecen en transacciones recientes."""
        client.force_login(user)

        income_cat = Category.objects.create(
            name="Test Cat",
            type=CategoryType.INCOME,
            is_system=True,
        )

        today = timezone.now().date()

        Income.objects.create(
            user=user,
            category=income_cat,
            description="Ingreso Test",
            amount=Decimal("500.00"),
            amount_ars=Decimal("500.00"),
            currency="ARS",
            exchange_rate=Decimal("1.00"),
            date=today,
        )

        response = client.get(reverse("reports:dashboard"))
        transactions = response.context["recent_transactions"]
        assert len(transactions) == 1
        assert transactions[0]["type"] == "income"
        assert transactions[0]["description"] == "Ingreso Test"

    def test_recent_transactions_mixed_and_sorted(self, client, user):
        """Verifica que las transacciones se mezclan y ordenan por fecha."""
        client.force_login(user)

        expense_cat = Category.objects.create(
            name="Expense Cat",
            type=CategoryType.EXPENSE,
            is_system=True,
        )
        income_cat = Category.objects.create(
            name="Income Cat",
            type=CategoryType.INCOME,
            is_system=True,
        )

        today = timezone.now().date()
        from datetime import timedelta

        # Crear transacciones con diferentes fechas
        Expense.objects.create(
            user=user,
            category=expense_cat,
            description="Gasto antiguo",
            amount=Decimal("100.00"),
            amount_ars=Decimal("100.00"),
            currency="ARS",
            exchange_rate=Decimal("1.00"),
            date=today - timedelta(days=5),
        )

        Income.objects.create(
            user=user,
            category=income_cat,
            description="Ingreso reciente",
            amount=Decimal("200.00"),
            amount_ars=Decimal("200.00"),
            currency="ARS",
            exchange_rate=Decimal("1.00"),
            date=today - timedelta(days=1),
        )

        Expense.objects.create(
            user=user,
            category=expense_cat,
            description="Gasto más reciente",
            amount=Decimal("50.00"),
            amount_ars=Decimal("50.00"),
            currency="ARS",
            exchange_rate=Decimal("1.00"),
            date=today,
        )

        response = client.get(reverse("reports:dashboard"))
        transactions = response.context["recent_transactions"]

        assert len(transactions) == 3
        # Verificar orden descendente por fecha
        assert transactions[0]["description"] == "Gasto más reciente"
        assert transactions[1]["description"] == "Ingreso reciente"
        assert transactions[2]["description"] == "Gasto antiguo"

    def test_recent_transactions_limit_to_8(self, client, user):
        """Verifica que solo se muestran las 8 transacciones más recientes."""
        client.force_login(user)

        expense_cat = Category.objects.create(
            name="Test Cat",
            type=CategoryType.EXPENSE,
            is_system=True,
        )

        today = timezone.now().date()
        from datetime import timedelta

        # Crear 12 gastos
        for i in range(12):
            Expense.objects.create(
                user=user,
                category=expense_cat,
                description=f"Gasto {i}",
                amount=Decimal("10.00"),
                amount_ars=Decimal("10.00"),
                currency="ARS",
                exchange_rate=Decimal("1.00"),
                date=today - timedelta(days=i),
            )

        response = client.get(reverse("reports:dashboard"))
        transactions = response.context["recent_transactions"]

        # Solo debe haber 8 transacciones
        assert len(transactions) == 8
        # Las más recientes primero (Gasto 0 es el más reciente)
        assert transactions[0]["description"] == "Gasto 0"
        assert transactions[7]["description"] == "Gasto 7"

    def test_recent_transactions_truly_recent(self, client, user):
        """
        Verifica que se muestran las 8 transacciones realmente más recientes,
        incluso si todas son del mismo tipo.
        """
        client.force_login(user)

        expense_cat = Category.objects.create(
            name="Expense Cat",
            type=CategoryType.EXPENSE,
            is_system=True,
        )
        income_cat = Category.objects.create(
            name="Income Cat",
            type=CategoryType.INCOME,
            is_system=True,
        )

        today = timezone.now().date()
        from datetime import timedelta

        # Crear 10 gastos recientes (días 0-9)
        for i in range(10):
            Expense.objects.create(
                user=user,
                category=expense_cat,
                description=f"Gasto reciente {i}",
                amount=Decimal("10.00"),
                amount_ars=Decimal("10.00"),
                currency="ARS",
                exchange_rate=Decimal("1.00"),
                date=today - timedelta(days=i),
            )

        # Crear 3 ingresos antiguos (días 20-22)
        for i in range(3):
            Income.objects.create(
                user=user,
                category=income_cat,
                description=f"Ingreso antiguo {i}",
                amount=Decimal("100.00"),
                amount_ars=Decimal("100.00"),
                currency="ARS",
                exchange_rate=Decimal("1.00"),
                date=today - timedelta(days=20 + i),
            )

        response = client.get(reverse("reports:dashboard"))
        transactions = response.context["recent_transactions"]

        # Debe mostrar los 8 gastos más recientes, NO mezclar con ingresos antiguos
        assert len(transactions) == 8
        # Todos deben ser gastos (los más recientes)
        for tx in transactions:
            assert tx["type"] == "expense"
            assert "Gasto reciente" in tx["description"]


@pytest.mark.django_db
class TestExpenseDistribution:
    """Tests para la distribución de gastos del dashboard."""

    def test_expense_distribution_empty(self, client, user):
        """Verifica distribución vacía sin gastos."""
        client.force_login(user)
        response = client.get(reverse("reports:dashboard"))
        assert response.context["expense_distribution"] == []
        assert response.context["chart_labels"] == []
        assert response.context["chart_data"] == []

    def test_expense_distribution_by_category(self, client, user):
        """Verifica que la distribución agrupa por categoría."""
        client.force_login(user)

        cat1 = Category.objects.create(
            name="Comida",
            type=CategoryType.EXPENSE,
            is_system=True,
            color="#FF0000",
        )
        cat2 = Category.objects.create(
            name="Transporte",
            type=CategoryType.EXPENSE,
            is_system=True,
            color="#00FF00",
        )

        today = timezone.now().date()

        # Dos gastos en Comida
        Expense.objects.create(
            user=user,
            category=cat1,
            description="Almuerzo",
            amount=Decimal("100.00"),
            amount_ars=Decimal("100.00"),
            currency="ARS",
            exchange_rate=Decimal("1.00"),
            date=today,
        )
        Expense.objects.create(
            user=user,
            category=cat1,
            description="Cena",
            amount=Decimal("150.00"),
            amount_ars=Decimal("150.00"),
            currency="ARS",
            exchange_rate=Decimal("1.00"),
            date=today,
        )

        # Un gasto en Transporte
        Expense.objects.create(
            user=user,
            category=cat2,
            description="Uber",
            amount=Decimal("50.00"),
            amount_ars=Decimal("50.00"),
            currency="ARS",
            exchange_rate=Decimal("1.00"),
            date=today,
        )

        response = client.get(reverse("reports:dashboard"))

        # Verificar que está ordenado por total descendente
        assert response.context["chart_labels"][0] == "Comida"
        assert response.context["chart_data"][0] == 250.0
        assert response.context["chart_labels"][1] == "Transporte"
        assert response.context["chart_data"][1]


@pytest.mark.django_db
class TestDashboardQueryPerformance:
    """Tests de performance para el dashboard."""

    def test_dashboard_empty_query_count(
        self, client, user, django_assert_max_num_queries, authenticated_client, url_helper
    ):
        """Verifica número de queries con dashboard vacío."""
        client.force_login(user)

        # Dashboard vacío debería usar pocas queries
        # Baseline: ~8 queries (session, user, balance, budgets, savings, etc.)
        with django_assert_max_num_queries(10):
            authenticated_client.get(url_helper("dashboard"))

    def test_dashboard_with_data_query_count(
        self,
        client,
        user,
        expense_category_factory,
        income_category_factory,
        expense_factory,
        income_factory,
        budget_factory,
        django_assert_max_num_queries,
        authenticated_client,
        url_helper,
    ):
        """Verifica que queries no escalan con cantidad de datos (N+1 check)."""
        client.force_login(user)

        today = timezone.now().date()
        from datetime import timedelta

        # Crear dataset representativo
        # 5 categorías de gasto
        expense_cats = [expense_category_factory(user, name=f"ExpCat{i}") for i in range(5)]

        # 3 categorías de ingreso
        income_cats = [income_category_factory(user, name=f"IncCat{i}") for i in range(3)]

        # 20 gastos distribuidos en categorías
        for i in range(20):
            expense_factory(
                user,
                expense_cats[i % 5],
                amount=Decimal("100.00"),
                date=today - timedelta(days=i % 30),
            )

        # 10 ingresos
        for i in range(10):
            income_factory(
                user,
                income_cats[i % 3],
                amount=Decimal("500.00"),
                date=today - timedelta(days=i % 30),
            )

        # 5 budgets
        for cat in expense_cats:
            budget_factory(
                user,
                category=cat,
                amount=Decimal("1000.00"),
            )

        # Con datos, queries deberían mantenerse constantes (no N+1)
        # Máximo 15 queries permitidas
        with django_assert_max_num_queries(10):
            response = authenticated_client.get(url_helper("dashboard"))

        assert response.status_code == 200

    def test_dashboard_large_dataset_no_n_plus_1(
        self,
        client,
        user,
        expense_category_factory,
        income_category_factory,
        expense_factory,
        income_factory,
        budget_factory,
        django_assert_max_num_queries,
        authenticated_client,
        url_helper,
    ):
        """
        Test con dataset grande para detectar N+1.
        Si hay N+1, las queries escalarían linealmente.
        """
        client.force_login(user)

        today = timezone.now().date()
        from datetime import timedelta

        # Dataset más grande
        # 10 categorías de gasto
        expense_cats = [expense_category_factory(user, name=f"BigExpCat{i}") for i in range(10)]

        # 5 categorías de ingreso
        income_cats = [income_category_factory(user, name=f"BigIncCat{i}") for i in range(5)]

        # 50 gastos
        for i in range(50):
            expense_factory(
                user,
                expense_cats[i % 10],
                amount=Decimal("50.00"),
                date=today - timedelta(days=i % 60),
            )

        # 30 ingresos
        for i in range(30):
            income_factory(
                user,
                income_cats[i % 5],
                amount=Decimal("200.00"),
                date=today - timedelta(days=i % 60),
            )

        # 10 budgets
        for cat in expense_cats:
            budget_factory(
                user,
                cat,
                month=today.month,
                year=today.year,
                amount=Decimal("500.00"),
            )

        # Aún con más datos, queries deben mantenerse ~igual
        # Si hay N+1, esto fallaría (sería 50+ queries)
        with django_assert_max_num_queries(10):
            response = authenticated_client.get(url_helper("dashboard"))

        assert response.status_code == 200
        assert len(response.context["recent_transactions"]) == 8
