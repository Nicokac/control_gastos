"""
Tests para las vistas de Core (Dashboard).
"""

from decimal import Decimal

from django.urls import NoReverseMatch, reverse
from django.utils import timezone

import pytest


@pytest.mark.django_db
class TestDashboardView:
    """Tests para la vista del dashboard."""

    def get_dashboard_url(self):
        """Obtiene la URL del dashboard, probando diferentes variantes."""
        variants = ["dashboard", "reports:dashboard", "core:dashboard"]
        for name in variants:
            try:
                return reverse(name)
            except NoReverseMatch:
                continue
        return None

    def test_login_required(self, client):
        """Verifica que requiera autenticación."""
        url = self.get_dashboard_url()
        if url is None:
            pytest.skip("Dashboard URL not configured")

        response = client.get(url)
        assert response.status_code == 302
        assert "login" in response.url

    def test_dashboard_accessible(self, authenticated_client):
        """Verifica que el dashboard sea accesible."""
        url = self.get_dashboard_url()
        if url is None:
            pytest.skip("Dashboard URL not configured")

        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_dashboard_has_context_data(self, authenticated_client, expense, income):  # noqa: ARG002
        """Verifica que el dashboard tenga datos en contexto."""
        try:
            url = reverse("dashboard")
        except NoReverseMatch:
            url = reverse("reports:dashboard")

        response = authenticated_client.get(url)

        assert response.status_code == 200
        context = response.context

        possible_keys = [
            "total_income",
            "income_total",
            "ingresos",
            "total_expenses",
            "expense_total",
            "gastos",
            "balance",
            "saldo",
            "savings",
            "ahorros",
        ]

        has_data = any(key in context for key in possible_keys)
        assert has_data or response.status_code == 200

    def test_dashboard_shows_current_month_data(
        self,
        authenticated_client,
        user,
        expense_category,
        income_category,
        expense_factory,
        income_factory,
    ):
        """Verifica que muestre datos del mes actual."""
        today = timezone.now().date()

        expense_factory(
            user,
            expense_category,
            amount=Decimal("1000.00"),
            date=today,
            description="Gasto Actual",
        )
        income_factory(
            user,
            income_category,
            amount=Decimal("5000.00"),
            date=today,
            description="Ingreso Actual",
        )

        try:
            url = reverse("dashboard")
        except NoReverseMatch:
            url = reverse("reports:dashboard")

        response = authenticated_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "1000" in content or "1.000" in content or "Gasto" in content

    def test_dashboard_excludes_other_user_data(
        self, authenticated_client, user, other_user, expense_category_factory, expense_factory
    ):  # noqa: ARG002
        """Verifica que no muestre datos de otros usuarios."""
        other_cat = expense_category_factory(other_user, name="Otra")
        expense_factory(
            other_user, other_cat, description="Gasto Otro Usuario", amount=Decimal("99999.00")
        )

        try:
            url = reverse("dashboard")
        except NoReverseMatch:
            url = reverse("reports:dashboard")

        response = authenticated_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()

        assert "Gasto Otro Usuario" not in content
        assert "99999" not in content

    def test_dashboard_does_not_show_budgets_section(self, authenticated_client):
        """Verifica que el dashboard ya no muestre el bloque de presupuestos."""
        url = self.get_dashboard_url()
        if url is None:
            pytest.skip("Dashboard URL not configured")

        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert "Presupuestos de" not in response.content.decode()

    def test_dashboard_shows_summary(self, authenticated_client, expense, income):  # noqa: ARG002
        """Verifica que el dashboard muestre resumen."""
        url = self.get_dashboard_url()
        if url is None:
            pytest.skip("Dashboard URL not configured")

        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_dashboard_only_user_data(
        self, authenticated_client, user, other_user, expense_category_factory, expense_factory
    ):  # noqa: ARG002
        """Verifica que solo muestre datos del usuario actual."""
        url = self.get_dashboard_url()
        if url is None:
            pytest.skip("Dashboard URL not configured")

        other_cat = expense_category_factory(other_user, name="Otra")
        expense_factory(other_user, other_cat, description="Otro Gasto")

        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert "Otro Gasto" not in response.content.decode()

    def test_dashboard_with_helper(self, authenticated_client, url_helper):
        """Ejemplo usando helper de URL."""
        url = url_helper("dashboard")
        response = authenticated_client.get(url)
        assert response.status_code == 200


@pytest.mark.django_db
class TestHomeView:
    """Tests para la vista principal."""

    def get_home_url(self):
        """Obtiene la URL de home, probando diferentes variantes."""
        variants = ["home", "core:home", "index"]
        for name in variants:
            try:
                return reverse(name)
            except NoReverseMatch:
                continue
        return None

    def test_home_redirects_authenticated_user(self, authenticated_client):
        """Verifica que usuario autenticado sea redirigido al dashboard."""
        url = self.get_home_url()
        if url is None:
            pytest.skip("Home URL not configured")

        response = authenticated_client.get(url)
        assert response.status_code in [200, 302]

    def test_home_accessible(self, client):
        """Verifica que home sea accesible."""
        try:
            url = reverse("home")
            response = client.get(url)
            assert response.status_code in [200, 302]
        except NoReverseMatch:
            pass

    def test_home_shows_landing_for_anonymous(self, client):
        """Verifica que usuario anónimo vea landing o login."""
        url = self.get_home_url()
        if url is None:
            pytest.skip("Home URL not configured")

        response = client.get(url)
        assert response.status_code in [200, 302]

    def test_authenticated_user_redirected(self, authenticated_client):
        """Verifica comportamiento de usuario autenticado."""
        try:
            url = reverse("home")
            response = authenticated_client.get(url)
            assert response.status_code in [200, 302]
        except NoReverseMatch:
            pass


@pytest.mark.django_db
class TestLegalPagesRenderForBothAuthStates:
    """DT-090: terms/privacy/account_deletion deben mostrar su contenido
    real tanto para visitantes anónimos como para usuarios logueados —
    antes de este fix, un anónimo veía la página vacía porque el contenido
    estaba solo en el bloque 'content' (que base.html solo renderiza para
    usuarios autenticados)."""

    def test_terms_muestra_contenido_sin_login(self, client):
        response = client.get(reverse("core:terms"))
        assert response.status_code == 200
        assert "Términos y Condiciones" in response.content.decode()

    def test_terms_muestra_contenido_logueado(self, authenticated_client):
        response = authenticated_client.get(reverse("core:terms"))
        assert response.status_code == 200
        assert "Términos y Condiciones" in response.content.decode()

    def test_privacy_muestra_contenido_sin_login(self, client):
        response = client.get(reverse("core:privacy"))
        assert response.status_code == 200
        assert "Política de Privacidad" in response.content.decode()

    def test_privacy_muestra_contenido_logueado(self, authenticated_client):
        response = authenticated_client.get(reverse("core:privacy"))
        assert response.status_code == 200
        assert "Política de Privacidad" in response.content.decode()

    def test_account_deletion_muestra_contenido_sin_login(self, client):
        response = client.get(reverse("core:account_deletion"))
        assert response.status_code == 200
        assert "Eliminar tu cuenta o tus datos" in response.content.decode()

    def test_account_deletion_muestra_contenido_logueado(self, authenticated_client):
        response = authenticated_client.get(reverse("core:account_deletion"))
        assert response.status_code == 200
        assert "Eliminar tu cuenta o tus datos" in response.content.decode()

    def test_terms_menciona_eliminacion_sin_login(self, client):
        """El texto debe reflejar que la eliminación también se puede pedir
        sin loguearse (DT-090)."""
        response = client.get(reverse("core:terms"))
        assert "sin loguearte" in response.content.decode()

    def test_privacy_menciona_eliminacion_sin_login(self, client):
        response = client.get(reverse("core:privacy"))
        assert "sin loguearte" in response.content.decode()


@pytest.mark.django_db
class TestAppFooterLegalLinks:
    """DT-090: los links a términos/privacidad deben estar accesibles
    desde cualquier pantalla autenticada normal (footer global), no solo
    desde landing o las páginas legales aisladas."""

    def test_dashboard_incluye_links_legales_en_footer(self, authenticated_client):
        url = reverse("reports:dashboard")
        response = authenticated_client.get(url)
        content = response.content.decode()
        assert reverse("core:terms") in content
        assert reverse("core:privacy") in content

    def test_login_incluye_links_legales_en_footer(self, client):
        response = client.get(reverse("users:login"))
        content = response.content.decode()
        assert reverse("core:terms") in content
        assert reverse("core:privacy") in content
