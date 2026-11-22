"""DT-062: descarga de todos los datos del usuario en un Excel."""

import datetime
import io
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone

import pytest
from openpyxl import load_workbook

from apps.categories.models import CategoryOverride, CategoryRule
from apps.recurring.models import RecurringExpense
from apps.recurring_income.models import RecurringIncome
from apps.shared_expenses.models import HouseholdMember, SharedExpense

SHEETS = [
    "Perfil",
    "Categorías",
    "Reglas de categorías",
    "Gastos",
    "Ingresos",
    "Gastos fijos",
    "Ingresos fijos",
    "Metas de ahorro",
    "Movimientos de ahorro",
    "Integrantes del hogar",
    "Gastos compartidos",
]


def _download(client):
    response = client.get(reverse("users:data_export"))
    assert response.status_code == 200
    return load_workbook(io.BytesIO(response.content))


def _rows(wb, sheet):
    return list(wb[sheet].iter_rows(min_row=2, values_only=True))


def _cargar_datos(user, expense_category_factory, income_category_factory, prefix, factories):
    expense_factory, income_factory, saving_factory, saving_movement_factory = factories
    gasto_cat = expense_category_factory(user=user, name=f"{prefix} Super")
    ingreso_cat = income_category_factory(user=user, name=f"{prefix} Sueldo")
    meta = saving_factory(user, name=f"{prefix} Vacaciones")
    fijo = RecurringExpense.objects.create(
        user=user, name=f"{prefix} Alquiler", category=gasto_cat, due_day=10
    )
    fijo_ingreso = RecurringIncome.objects.create(
        user=user, name=f"{prefix} Sueldo fijo", category=ingreso_cat, expected_day=5
    )
    expense_factory(
        user,
        gasto_cat,
        description=f"{prefix} compra",
        amount=Decimal("1234.56"),
        date=datetime.date(2026, 3, 15),
        payment_method="DEBIT",
        saving=meta,
        recurring=fijo,
    )
    income_factory(user, ingreso_cat, description=f"{prefix} cobro", recurring=fijo_ingreso)
    saving_movement_factory(meta, description=f"{prefix} aporte")
    CategoryRule.objects.create(user=user, pattern=f"{prefix} coto", category=gasto_cat)
    miembro = HouseholdMember.objects.create(user=user, name=f"{prefix} Ana")
    SharedExpense.objects.create(
        user=user,
        amount=Decimal("500.00"),
        currency="ARS",
        exchange_rate=Decimal("1.00"),
        date=timezone.localdate(),
        description=f"{prefix} pizza",
        category=gasto_cat,
        paid_by=miembro,
    )


@pytest.fixture
def factories(expense_factory, income_factory, saving_factory, saving_movement_factory):
    return expense_factory, income_factory, saving_factory, saving_movement_factory


@pytest.mark.django_db
class TestDataExportView:
    @pytest.mark.parametrize("page", ["users:profile", "users:delete_account"])
    def test_mi_cuenta_y_eliminar_cuenta_ofrecen_la_descarga(self, authenticated_client, page):
        content = authenticated_client.get(reverse(page)).content.decode()
        assert reverse("users:data_export") in content

    def test_requiere_login(self, client):
        response = client.get(reverse("users:data_export"))
        assert response.status_code == 302
        assert reverse("users:login") in response.url

    def test_descarga_un_excel_con_todas_las_hojas(self, authenticated_client):
        response = authenticated_client.get(reverse("users:data_export"))

        assert response["Content-Type"] == (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        assert response["Content-Disposition"].startswith('attachment; filename="mis datos ')
        wb = load_workbook(io.BytesIO(response.content))
        assert wb.sheetnames == SHEETS

    def test_usuario_sin_datos_recibe_hojas_vacias(self, authenticated_client):
        wb = _download(authenticated_client)
        for sheet in SHEETS[1:]:
            assert _rows(wb, sheet) == []

    def test_el_perfil_no_incluye_la_contrasena(self, authenticated_client, user):
        wb = _download(authenticated_client)
        perfil = dict(_rows(wb, "Perfil"))

        assert perfil["Usuario"] == user.username
        assert perfil["Email"] == user.email
        assert "Contraseña" not in perfil
        assert user.password not in str(_rows(wb, "Perfil"))

    def test_exporta_cada_entidad_con_nombres_legibles(
        self,
        authenticated_client,
        user,
        expense_category_factory,
        income_category_factory,
        factories,
    ):
        _cargar_datos(user, expense_category_factory, income_category_factory, "Mio", factories)
        wb = _download(authenticated_client)

        gasto = _rows(wb, "Gastos")[0]
        assert gasto[0] == datetime.datetime(2026, 3, 15)
        assert gasto[1:4] == ("Otros gastos", "Mio Super", "Mio compra")
        assert gasto[4] == pytest.approx(1234.56)
        assert gasto[8:] == ("Tarjeta de Débito", "Mio Vacaciones", "Mio Alquiler")
        assert wb["Gastos"]["A2"].number_format == "DD/MM/YYYY"

        assert _rows(wb, "Ingresos")[0][1:4] == ("Otros ingresos", "Mio Sueldo", "Mio cobro")
        assert _rows(wb, "Ingresos")[0][-1] == "Mio Sueldo fijo"
        assert _rows(wb, "Gastos fijos")[0][:4] == ("Mio Alquiler", "Otros gastos", "Mio Super", 10)
        assert _rows(wb, "Ingresos fijos")[0][:4] == (
            "Mio Sueldo fijo",
            "Otros ingresos",
            "Mio Sueldo",
            5,
        )
        assert _rows(wb, "Metas de ahorro")[0][0] == "Mio Vacaciones"
        assert _rows(wb, "Movimientos de ahorro")[0][1:3] == ("Mio Vacaciones", "Depósito")
        assert _rows(wb, "Reglas de categorías") == [("Mio coto", "Otros gastos", "Mio Super")]
        assert _rows(wb, "Integrantes del hogar") == [("Mio Ana",)]
        assert _rows(wb, "Gastos compartidos")[0][3] == "Mio pizza"
        assert _rows(wb, "Gastos compartidos")[0][-1] == "Mio Ana"

    def test_no_incluye_datos_de_otro_usuario(
        self,
        authenticated_client,
        user,
        other_user,
        expense_category_factory,
        income_category_factory,
        factories,
    ):
        _cargar_datos(user, expense_category_factory, income_category_factory, "Mio", factories)
        _cargar_datos(
            other_user, expense_category_factory, income_category_factory, "Ajeno", factories
        )
        wb = _download(authenticated_client)

        contenido = str([_rows(wb, sheet) for sheet in SHEETS])
        assert "Mio" in contenido
        assert "Ajeno" not in contenido
        assert other_user.email not in contenido

    def test_categorias_propias_y_de_sistema_ocultas(
        self, authenticated_client, user, expense_category_factory, system_expense_category
    ):
        expense_category_factory(user=user, name="Propia visible")
        expense_category_factory(user=None, name="Sistema visible", is_system=True)
        CategoryOverride.objects.create(user=user, category=system_expense_category, is_hidden=True)

        wb = _download(authenticated_client)
        categorias = {row[2]: (row[3], row[4]) for row in _rows(wb, "Categorías")}

        assert categorias == {
            "Propia visible": ("Propia", "No"),
            "Otros Gastos Test": ("Sistema", "Sí"),
        }

    def test_categorias_de_sistema_con_limite_propio(
        self, authenticated_client, user, expense_category_factory, system_expense_category
    ):
        expense_category_factory(user=None, name="Sistema sin limite", is_system=True)
        CategoryOverride.objects.create(
            user=user, category=system_expense_category, monthly_alert_threshold=Decimal("5000")
        )

        wb = _download(authenticated_client)
        categorias = {row[2]: (row[3], row[4], row[5]) for row in _rows(wb, "Categorías")}

        assert categorias == {"Otros Gastos Test": ("Sistema", "No", 5000)}

    def test_las_consultas_no_crecen_con_la_cantidad_de_registros(
        self,
        authenticated_client,
        user,
        expense_category_factory,
        income_category_factory,
        factories,
        django_assert_max_num_queries,
    ):
        for prefix in ("A", "B", "C"):
            _cargar_datos(
                user, expense_category_factory, income_category_factory, prefix, factories
            )

        with django_assert_max_num_queries(20):
            wb = _download(authenticated_client)

        assert len(_rows(wb, "Gastos")) == 3
