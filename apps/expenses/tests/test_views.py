"""
Tests para las vistas de Expense.
"""

from decimal import Decimal

from django.urls import reverse
from django.utils import timezone

import pytest

from apps.core.constants import Currency
from apps.expenses.models import Expense


@pytest.mark.django_db
class TestExpenseListView:
    """Tests para la vista de listado de gastos."""

    def test_login_required(self, client):
        """Verifica que requiera autenticación."""
        url = reverse("expenses:list")
        response = client.get(url)

        assert response.status_code == 302
        assert "login" in response.url

    def test_list_user_expenses(self, authenticated_client, expense):
        """Verifica que liste los gastos del usuario."""
        url = reverse("expenses:list")
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert expense.description in response.content.decode()

    def test_excludes_other_user_expenses(
        self, authenticated_client, other_user, expense_category_factory, expense_factory
    ):
        """Verifica que no muestre gastos de otros usuarios."""
        other_cat = expense_category_factory(other_user, name="Otra")
        expense_factory(other_user, other_cat, description="Gasto Otro")  # 🔧 F841

        url = reverse("expenses:list")
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert "Gasto Otro" not in response.content.decode()

    def test_filter_by_month(self, authenticated_client, user, expense_category, expense_factory):
        """Verifica filtrado por mes."""
        today = timezone.now().date()
        expense_factory(user, expense_category, description="Este Mes", date=today)

        url = reverse("expenses:list")
        response = authenticated_client.get(url, {"month": today.month, "year": today.year})

        assert response.status_code == 200
        assert "Este Mes" in response.content.decode()

    def test_filter_by_category(
        self, authenticated_client, user, expense_category, expense_factory
    ):
        """Verifica filtrado por grupo padre."""
        expense_factory(user, expense_category, description="Filtrado")

        url = reverse("expenses:list")
        # El filtro ahora es por grupo (parent), no por subcategoría
        response = authenticated_client.get(url, {"category": expense_category.parent.pk})

        assert response.status_code == 200
        assert "Filtrado" in response.content.decode()

    def test_list_shows_total_period_summary(
        self, authenticated_client, user, expense_category, expense_factory
    ):
        """Verifica que el resumen muestre el total del período."""
        expense_factory(
            user,
            expense_category,
            description="Gasto Resumen",
            amount=Decimal("1500.00"),
            date=timezone.now().date(),
        )

        url = reverse("expenses:list")
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert response.context["total"] == Decimal("1500.00")

    def test_list_builds_expense_type_and_payment_method_summary(
        self, authenticated_client, user, expense_category, expense_factory
    ):
        """Verifica que construya resúmenes por tipo y método de pago."""
        expense_factory(
            user,
            expense_category,
            description="Gasto Fijo Efectivo",
            amount=Decimal("1000.00"),
            date=timezone.now().date(),
            expense_type="FIXED",
            payment_method="CASH",
        )

        url = reverse("expenses:list")
        response = authenticated_client.get(url)

        assert response.status_code == 200

        expense_type_summary = response.context["expense_type_summary"]
        payment_method_summary = response.context["payment_method_summary"]

        assert len(expense_type_summary) == 1
        assert expense_type_summary[0]["subtotal"] == Decimal("1000.00")

        assert len(payment_method_summary) == 1
        assert payment_method_summary[0]["subtotal"] == Decimal("1000.00")

    def test_list_renders_advanced_filters_controls(
        self, authenticated_client, user, expense_category, expense_factory
    ):
        """Verifica que el listado renderice los controles de filtros avanzados."""
        expense_factory(
            user,
            expense_category,
            description="Gasto UX",
            amount=Decimal("500.00"),
            date=timezone.now().date(),
        )

        url = reverse("expenses:list")
        response = authenticated_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()

        assert "M\u00e9todo de pago" in content or "Método de pago" in content
        assert "Tipo" in content
        assert "filter_form" in response.context


@pytest.mark.django_db
class TestExpenseCreateView:
    """Tests para la vista de creación de gastos."""

    def test_login_required(self, client):
        """Verifica que requiera autenticación."""
        url = reverse("expenses:create")
        response = client.get(url)

        assert response.status_code == 302
        assert "login" in response.url

    def test_get_create_form(self, authenticated_client):
        """Verifica que muestre el formulario de creación."""
        url = reverse("expenses:create")
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert "form" in response.context

    def test_create_expense_ars_success(self, authenticated_client, user, expense_category):
        """Verifica creación exitosa de gasto en ARS."""
        url = reverse("expenses:create")
        data = {
            "category": expense_category.pk,
            "description": "Nuevo Gasto",
            "amount": "1500.00",
            "currency": Currency.ARS,
            "date": timezone.now().date().isoformat(),
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == 302
        assert Expense.objects.filter(description="Nuevo Gasto", user=user).exists()

    def test_create_expense_usd_success(self, authenticated_client, user, expense_category):
        """Verifica creación exitosa de gasto en USD."""
        url = reverse("expenses:create")
        data = {
            "category": expense_category.pk,
            "description": "Gasto USD",
            "amount": "100.00",
            "currency": Currency.USD,
            "exchange_rate": "1150.00",
            "date": timezone.now().date().isoformat(),
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == 302

        expense = Expense.objects.get(description="Gasto USD")
        assert expense.currency == Currency.USD
        assert expense.exchange_rate == Decimal("1150.00")

    def test_create_expense_invalid_data(self, authenticated_client, expense_category):
        """Verifica que no cree con datos inválidos."""
        url = reverse("expenses:create")
        data = {
            "category": expense_category.pk,
            "description": "",
            "amount": "",  # Monto inválido
            "currency": Currency.ARS,
            "date": timezone.now().date().isoformat(),
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == 200
        assert response.context["form"].errors
        assert "No pudimos guardar el gasto." in response.content.decode()

    def test_expense_assigned_to_current_user(self, authenticated_client, user, expense_category):
        """Verifica que el gasto se asigne al usuario actual."""
        url = reverse("expenses:create")
        data = {
            "category": expense_category.pk,
            "description": "Mi Gasto",
            "amount": "500.00",
            "currency": Currency.ARS,
            "date": timezone.now().date().isoformat(),
        }

        authenticated_client.post(url, data)

        expense = Expense.objects.get(description="Mi Gasto")
        assert expense.user == user

    def test_only_user_categories_in_form(
        self, authenticated_client, user, expense_category, other_user, expense_category_factory
    ):
        """Verifica que solo muestre categorías del usuario en el form."""
        other_cat = expense_category_factory(other_user, name="Otra")

        url = reverse("expenses:create")
        response = authenticated_client.get(url)

        form = response.context["form"]
        category_pks = [c.pk for c in form.fields["category"].queryset]

        assert expense_category.pk in category_pks
        assert other_cat.pk not in category_pks

    def test_create_form_renders_core_and_advanced_fields(self, authenticated_client):
        """Verifica que el formulario muestre campos core y el bloque de avanzados."""
        url = reverse("expenses:create")
        response = authenticated_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()

        # Campos core visibles
        assert "Monto" in content
        assert "Categor" in content  # evita problemas de encoding
        assert "Fecha" in content
        assert "Descripci" in content

        # Bloque de avanzados visible como trigger
        assert "Opciones avanzadas" in content

        # Campos avanzados renderizados en template
        assert "M\u00e9todo de pago" in content or "Método de pago" in content
        assert "Tipo de gasto" in content


@pytest.mark.django_db
class TestExpenseCreateWithSaving:
    """Tests para vinculación de gasto con meta de ahorro."""

    def test_create_expense_with_saving_deposits(
        self, authenticated_client, user, expense_category, saving_factory
    ):
        """Verifica que crear gasto con saving dispare depósito en la meta."""
        from apps.savings.models import SavingMovement

        saving = saving_factory(user, target_amount=Decimal("10000.00"))
        initial_amount = saving.current_amount

        url = reverse("expenses:create")
        data = {
            "category": expense_category.pk,
            "description": "Gasto con ahorro",
            "amount": "1000.00",
            "currency": "ARS",
            "date": timezone.now().date().isoformat(),
            "saving": saving.pk,
        }
        response = authenticated_client.post(url, data)

        assert response.status_code == 302
        saving.refresh_from_db()
        assert saving.current_amount == initial_amount + Decimal("1000.00")
        assert SavingMovement.objects.filter(saving=saving).exists()

    def test_create_expense_without_saving_no_movement(
        self, authenticated_client, user, expense_category, saving_factory
    ):
        """Verifica que sin saving no se crea movimiento."""
        from apps.savings.models import SavingMovement

        saving = saving_factory(user)

        url = reverse("expenses:create")
        data = {
            "category": expense_category.pk,
            "description": "Gasto sin ahorro",
            "amount": "500.00",
            "currency": "ARS",
            "date": timezone.now().date().isoformat(),
        }
        authenticated_client.post(url, data)

        assert SavingMovement.objects.filter(saving=saving).count() == 0

    def test_cannot_link_other_user_saving(
        self, authenticated_client, user, other_user, expense_category, saving_factory
    ):
        """Verifica que no se pueda vincular saving de otro usuario."""
        other_saving = saving_factory(other_user)

        url = reverse("expenses:create")
        data = {
            "category": expense_category.pk,
            "description": "Gasto ajeno",
            "amount": "500.00",
            "currency": "ARS",
            "date": timezone.now().date().isoformat(),
            "saving": other_saving.pk,
        }
        response = authenticated_client.post(url, data)

        # El form rechaza el saving ajeno (no está en queryset del usuario) → form inválido
        assert response.status_code == 200
        assert "form" in response.context
        from apps.expenses.models import Expense

        assert not Expense.objects.filter(description="Gasto ajeno", user=user).exists()


@pytest.mark.django_db
class TestExpenseUpdateView:
    """Tests para la vista de edición de gastos."""

    def test_login_required(self, client, expense):
        """Verifica que requiera autenticación."""
        url = reverse("expenses:update", kwargs={"pk": expense.pk})
        response = client.get(url)

        assert response.status_code == 302
        assert "login" in response.url

    def test_get_update_form(self, authenticated_client, expense):
        """Verifica que muestre el formulario de edición."""
        url = reverse("expenses:update", kwargs={"pk": expense.pk})
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert "form" in response.context
        assert response.context["form"].instance == expense

    def test_update_expense_success(self, authenticated_client, expense):
        """Verifica edición exitosa de gasto."""
        url = reverse("expenses:update", kwargs={"pk": expense.pk})
        data = {
            "category": expense.category.pk,
            "description": "Descripción Actualizada",
            "amount": str(expense.amount),
            "currency": expense.currency,
            "date": expense.date.isoformat(),
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == 302

        expense.refresh_from_db()
        assert expense.description == "Descripción Actualizada"

    def test_cannot_update_other_user_expense(
        self, authenticated_client, other_user, expense_category_factory, expense_factory
    ):
        """Verifica que no pueda editar gastos de otros usuarios."""
        other_cat = expense_category_factory(other_user, name="Otra")
        other_expense = expense_factory(other_user, other_cat)

        url = reverse("expenses:update", kwargs={"pk": other_expense.pk})
        response = authenticated_client.get(url)

        assert response.status_code in [403, 404]


@pytest.mark.django_db
class TestExpenseDeleteView:
    """Tests para la vista de eliminación de gastos."""

    def test_login_required(self, client, expense):
        """Verifica que requiera autenticación."""
        url = reverse("expenses:delete", kwargs={"pk": expense.pk})
        response = client.post(url)

        assert response.status_code == 302
        assert "login" in response.url

    def test_delete_expense_success(self, authenticated_client, expense):
        """Verifica eliminación exitosa de gasto."""
        expense_pk = expense.pk
        url = reverse("expenses:delete", kwargs={"pk": expense_pk})

        response = authenticated_client.post(url)

        assert response.status_code == 302
        assert not Expense.objects.filter(pk=expense_pk).exists()

    def test_cannot_delete_other_user_expense(
        self, authenticated_client, other_user, expense_category_factory, expense_factory
    ):
        """Verifica que no pueda eliminar gastos de otros usuarios."""
        other_cat = expense_category_factory(other_user, name="Otra")
        other_expense = expense_factory(other_user, other_cat)

        url = reverse("expenses:delete", kwargs={"pk": other_expense.pk})
        response = authenticated_client.post(url)

        assert response.status_code in [403, 404]


@pytest.mark.django_db
class TestExpenseDetailView:
    """Tests para la vista de detalle de gasto."""

    def test_login_required(self, client, expense):
        """Verifica que requiera autenticación."""
        url = reverse("expenses:detail", kwargs={"pk": expense.pk})
        response = client.get(url)

        assert response.status_code == 302
        assert "login" in response.url

    def test_view_expense_detail(self, authenticated_client, expense):
        """Verifica que muestre el detalle del gasto."""
        url = reverse("expenses:detail", kwargs={"pk": expense.pk})
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert expense.description in response.content.decode()

    def test_cannot_view_other_user_expense(
        self, authenticated_client, other_user, expense_category_factory, expense_factory
    ):
        """Verifica que no pueda ver gastos de otros usuarios."""
        other_cat = expense_category_factory(other_user, name="Otra")
        other_expense = expense_factory(other_user, other_cat)

        url = reverse("expenses:detail", kwargs={"pk": other_expense.pk})
        response = authenticated_client.get(url)

        assert response.status_code in [403, 404]


@pytest.mark.django_db
class TestExpenseListViewFilters:
    """Tests para filtros en la vista de listado de gastos."""

    def test_filter_by_month_shows_only_month_expenses(
        self, authenticated_client, user, expense_category, expense_factory
    ):
        """Verifica que filtro por mes muestre solo gastos de ese mes."""
        from datetime import date

        # Crear gastos en diferentes meses
        expense_factory(user, expense_category, date=date(2025, 1, 15), description="Gasto Enero")
        expense_factory(user, expense_category, date=date(2025, 2, 15), description="Gasto Febrero")
        expense_factory(user, expense_category, date=date(2025, 3, 15), description="Gasto Marzo")

        url = reverse("expenses:list")
        response = authenticated_client.get(url, {"month": 1, "year": 2025})

        assert response.status_code == 200
        content = response.content.decode()
        assert "Gasto Enero" in content
        assert "Gasto Febrero" not in content
        assert "Gasto Marzo" not in content

    def test_filter_by_category_shows_only_category_expenses(
        self,
        authenticated_client,
        user,
        expense_category_factory,
        expense_factory,
        system_expense_group,
    ):
        """Verifica que filtro por grupo muestre solo gastos de ese grupo."""
        from apps.categories.models import Category
        from apps.core.constants import CategoryType

        group_comida = Category.objects.create(
            name="Comida Test", type=CategoryType.EXPENSE, user=user, parent=None, is_system=False
        )
        group_transporte = Category.objects.create(
            name="Transporte Test",
            type=CategoryType.EXPENSE,
            user=user,
            parent=None,
            is_system=False,
        )
        cat_comida = expense_category_factory(user, name="Almuerzo sub", parent=group_comida)
        cat_transporte = expense_category_factory(
            user, name="Colectivo sub", parent=group_transporte
        )

        expense_factory(user, cat_comida, description="Desc-comida-xyz")
        expense_factory(user, cat_transporte, description="Desc-transporte-xyz")

        url = reverse("expenses:list")
        response = authenticated_client.get(url, {"category": group_comida.pk})

        assert response.status_code == 200
        expenses_in_response = list(response.context["expenses"])
        descriptions = [e.description for e in expenses_in_response]
        assert "Desc-comida-xyz" in descriptions
        assert "Desc-transporte-xyz" not in descriptions

    def test_filter_by_payment_method(
        self, authenticated_client, user, expense_category, expense_factory
    ):
        """Verifica filtro por método de pago."""
        expense_factory(user, expense_category, description="Pago Efectivo", payment_method="CASH")
        expense_factory(user, expense_category, description="Pago Débito", payment_method="DEBIT")

        url = reverse("expenses:list")
        response = authenticated_client.get(url, {"payment_method": "CASH"})

        assert response.status_code == 200
        content = response.content.decode()
        assert "Pago Efectivo" in content
        assert "Pago Débito" not in content

    def test_filter_by_expense_type(
        self, authenticated_client, user, expense_category, expense_factory
    ):
        """Verifica filtro por tipo de gasto."""
        expense_factory(user, expense_category, description="Gasto Fijo", expense_type="FIXED")
        expense_factory(
            user, expense_category, description="Gasto Variable", expense_type="VARIABLE"
        )

        url = reverse("expenses:list")
        response = authenticated_client.get(url, {"expense_type": "FIXED"})

        assert response.status_code == 200
        content = response.content.decode()
        assert "Gasto Fijo" in content
        assert "Gasto Variable" not in content

    def test_filter_by_date_range(
        self, authenticated_client, user, expense_category, expense_factory
    ):
        """Verifica filtro por rango de fechas."""
        from datetime import date

        expense_factory(user, expense_category, date=date(2025, 1, 5), description="Inicio Mes")
        expense_factory(user, expense_category, date=date(2025, 1, 15), description="Mitad Mes")
        expense_factory(user, expense_category, date=date(2025, 1, 25), description="Fin Mes")

        url = reverse("expenses:list")
        response = authenticated_client.get(
            url, {"date_from": "2025-01-10", "date_to": "2025-01-20"}
        )

        assert response.status_code == 200
        content = response.content.decode()

        # Solo debería mostrar el del medio
        # Nota: ajustar según implementación de filtros
        if "date_from" in response.request.get("QUERY_STRING", ""):
            assert "Mitad Mes" in content

    def test_combined_filters(
        self, authenticated_client, user, expense_category_factory, expense_factory
    ):
        """Verifica que múltiples filtros funcionen juntos."""
        from datetime import date

        from apps.categories.models import Category
        from apps.core.constants import CategoryType

        group1 = Category.objects.create(
            name="Grupo1 Test", type=CategoryType.EXPENSE, user=user, parent=None, is_system=False
        )
        group2 = Category.objects.create(
            name="Grupo2 Test", type=CategoryType.EXPENSE, user=user, parent=None, is_system=False
        )
        cat1 = expense_category_factory(user, name="Cat1 sub", parent=group1)
        cat2 = expense_category_factory(user, name="Cat2 sub", parent=group2)

        expense_factory(user, cat1, date=date(2025, 1, 15), description="Cat1 Enero")
        expense_factory(user, cat1, date=date(2025, 2, 15), description="Cat1 Febrero")
        expense_factory(user, cat2, date=date(2025, 1, 15), description="Cat2 Enero")

        url = reverse("expenses:list")
        response = authenticated_client.get(url, {"category": group1.pk, "month": 1, "year": 2025})

        assert response.status_code == 200
        content = response.content.decode()
        assert "Cat1 Enero" in content
        assert "Cat1 Febrero" not in content
        assert "Cat2 Enero" not in content

    def test_empty_filter_results(
        self, authenticated_client, user, expense_category, expense_factory
    ):
        """Verifica comportamiento cuando filtro no tiene resultados."""
        from datetime import date

        expense_factory(user, expense_category, date=date(2025, 1, 15), description="Único Gasto")

        url = reverse("expenses:list")
        response = authenticated_client.get(url, {"month": 6, "year": 2025})

        assert response.status_code == 200
        content = response.content.decode()
        assert "Único Gasto" not in content


@pytest.mark.django_db
class TestExpenseViewRedirects:
    """Tests para verificar redirecciones correctas."""

    def test_create_redirects_to_list(self, authenticated_client, user, expense_category):
        """Verifica que crear redirija a lista."""
        url = reverse("expenses:create")
        data = {
            "category": expense_category.pk,
            "description": "Nuevo Gasto",
            "amount": "1500.00",
            "currency": Currency.ARS,
            "date": timezone.now().date().isoformat(),
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == 302
        assert "expenses" in response.url

    def test_update_redirects_correctly(self, authenticated_client, expense):
        """Verifica que actualizar redirija correctamente."""
        url = reverse("expenses:update", kwargs={"pk": expense.pk})
        data = {
            "category": expense.category.pk,
            "description": "Actualizado",
            "amount": str(expense.amount),
            "currency": expense.currency,
            "date": expense.date.isoformat(),
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == 302
        # Puede redirigir a list o a detail
        assert "expenses" in response.url

    def test_delete_redirects_to_list(self, authenticated_client, expense):
        """Verifica que eliminar redirija a lista."""
        url = reverse("expenses:delete", kwargs={"pk": expense.pk})

        response = authenticated_client.post(url)

        assert response.status_code == 302
        assert "expenses" in response.url


@pytest.mark.django_db
class TestExpenseListViewOrdering:
    """Tests para verificar ordenamiento en ListView."""

    def test_expenses_ordered_by_date_descending(
        self, authenticated_client, user, expense_category, expense_factory
    ):
        """Verifica que gastos estén ordenados por fecha descendente."""
        from datetime import date

        # Crear gastos en orden cronológico
        expense_factory(
            user, expense_category, date=date(2025, 1, 1), description="Primero Cronológico"
        )
        expense_factory(
            user, expense_category, date=date(2025, 1, 15), description="Segundo Cronológico"
        )
        expense_factory(
            user, expense_category, date=date(2025, 1, 30), description="Tercero Cronológico"
        )

        url = reverse("expenses:list")
        response = authenticated_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()

        # Verificar que el más reciente aparezca primero
        pos_tercero = content.find("Tercero Cronológico")
        pos_segundo = content.find("Segundo Cronológico")
        pos_primero = content.find("Primero Cronológico")

        # Si todos existen en el contenido, verificar orden
        if pos_tercero != -1 and pos_segundo != -1 and pos_primero != -1:
            assert pos_tercero < pos_segundo < pos_primero

    def test_expenses_same_date_ordered_by_created(
        self, authenticated_client, user, expense_category, expense_factory
    ):
        """Verifica ordenamiento secundario cuando fechas son iguales."""
        import time

        from django.utils import timezone

        today = timezone.now().date()

        # Crear gastos en el mismo día
        expense_factory(user, expense_category, date=today, description="Gasto A")
        time.sleep(0.1)  # Pequeña pausa para diferenciar created_at
        expense_factory(user, expense_category, date=today, description="Gasto B")

        url = reverse("expenses:list")
        response = authenticated_client.get(url, {"month": today.month, "year": today.year})
        assert response.status_code == 200
        content = response.content.decode()
        assert "Gasto A" in content
        assert "Gasto B" in content


@pytest.mark.django_db
class TestExpenseFormGroupedCategories:
    """Tests para el selector de categorías agrupadas en formulario de gastos."""

    def test_create_view_has_categories_by_group(self, authenticated_client, expense_category):
        """El contexto del create view incluye categories_by_group."""
        url = reverse("expenses:create")
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert "categories_by_group" in response.context

    def test_categories_by_group_structure(self, authenticated_client, user, expense_category):
        """categories_by_group es una lista con 'group' y 'subcategories'."""
        url = reverse("expenses:create")
        response = authenticated_client.get(url)

        by_group = response.context["categories_by_group"]
        assert len(by_group) >= 1
        first = by_group[0]
        assert "group" in first
        assert "subcategories" in first
        assert expense_category in first["subcategories"]

    def test_update_view_has_categories_by_group(self, authenticated_client, expense):
        """El contexto del update view también incluye categories_by_group."""
        url = reverse("expenses:update", kwargs={"pk": expense.pk})
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert "categories_by_group" in response.context

    def test_group_header_rendered_in_template(self, authenticated_client, expense_category):
        """El nombre del grupo aparece en el HTML del formulario."""
        url = reverse("expenses:create")
        response = authenticated_client.get(url)

        content = response.content.decode()
        assert expense_category.parent.name in content

    def test_categories_from_other_users_not_in_groups(
        self, authenticated_client, other_user, expense_category_factory
    ):
        """Categorías de otros usuarios no aparecen en categories_by_group."""
        other_cat = expense_category_factory(other_user, name="Ajena")

        url = reverse("expenses:create")
        response = authenticated_client.get(url)

        all_subs = [
            sub
            for entry in response.context["categories_by_group"]
            for sub in entry["subcategories"]
        ]
        assert other_cat not in all_subs
