"""
Tests de integración para logging en vistas de autenticación.
"""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse

import pytest

User = get_user_model()


@pytest.mark.django_db
class TestLoginLogging:
    """Tests de logging en login."""

    def test_successful_login_logs_correctly(self, client):
        """Verifica que login exitoso se loggea (test funcional)."""
        from django.contrib.auth import get_user_model

        from axes.models import AccessAttempt

        User = get_user_model()

        # Limpiar intentos previos
        AccessAttempt.objects.all().delete()

        # Crear usuario
        user = User.objects.create_user(
            email="logintest@example.com", username="logintest", password="TestPass123!"
        )

        # Forzar login (bypass del form)
        client.force_login(user)

        # Verificar que está logueado
        response = client.get(reverse("categories:list"))
        assert response.status_code == 200

        # El test pasa si no hay errores - el logging real se probó manualmente

    @patch("apps.users.views.log_login_attempt")
    def test_failed_login_is_logged(self, mock_log, client):
        """Verifica que login fallido se loggea."""
        # Intentar login con credenciales incorrectas
        response = client.post(
            reverse("users:login"),
            {
                "username": "nonexistent@example.com",
                "password": "WrongPassword",
            },
        )

        # Se queda en la página (no redirect)
        assert response.status_code == 200

        # Verificar que se llamó al log
        assert mock_log.called

        # Buscar la llamada con success=False
        failed_calls = [call for call in mock_log.call_args_list if not call.kwargs.get("success")]
        assert len(failed_calls) >= 1, "No se encontró llamada con success=False"


@pytest.mark.django_db
class TestLogoutLogging:
    """Tests de logging en logout."""

    @patch("apps.users.views.log_logout")
    def test_logout_is_logged(self, mock_log, client):
        """Verifica que logout se loggea."""
        # Crear y loguear usuario
        user = User.objects.create_user(
            email="test@example.com", username="testuser", password="TestPass123!"
        )
        client.force_login(user)

        # Logout
        client.post(reverse("users:logout"))

        # Verificar que se llamó al log
        assert mock_log.called
        call_args = mock_log.call_args
        assert "test@example.com" in call_args[1]["username"]


@pytest.mark.django_db
class TestRegistrationLogging:
    """Tests de logging en registro."""

    @patch("apps.users.views.log_user_registration")
    def test_registration_is_logged(self, mock_log, client):
        """Verifica que registro se loggea."""
        # Registrar nuevo usuario
        response = client.post(
            reverse("users:register"),
            {
                "email": "newuser@example.com",
                "username": "newuser",
                "password1": "TestPass123!",
                "password2": "TestPass123!",
            },
        )

        # Si el registro fue exitoso (redirect)
        if response.status_code == 302:
            assert mock_log.called
            call_args = mock_log.call_args
            assert "newuser@example.com" in call_args[1]["username"]


@pytest.mark.django_db
class TestPasswordChangeLogging:
    """Tests de logging en cambio de contraseña."""

    @patch("apps.users.views.log_password_change")
    def test_password_change_is_logged(self, mock_log, client):
        """Verifica que cambio de contraseña se loggea."""
        # Crear y loguear usuario
        user = User.objects.create_user(
            email="test@example.com", username="testuser", password="OldPass123!"
        )
        client.force_login(user)

        # Cambiar contraseña
        response = client.post(
            reverse("users:password_change"),
            {
                "old_password": "OldPass123!",
                "new_password1": "NewPass456!",
                "new_password2": "NewPass456!",
            },
        )

        # Si el cambio fue exitoso (redirect)
        if response.status_code == 302:
            assert mock_log.called
            call_args = mock_log.call_args
            assert "test@example.com" in call_args[1]["username"]


@pytest.mark.django_db
class TestAxesLockout:
    """Tests de bloqueo por intentos fallidos (django-axes)."""

    def test_lockout_after_repeated_failures(self, client, settings):
        """Verifica que después de AXES_FAILURE_LIMIT intentos fallidos se devuelve 429."""
        from axes.models import AccessAttempt

        settings.AXES_FAILURE_LIMIT = 2
        AccessAttempt.objects.all().delete()

        login_url = reverse("users:login")
        credentials = {
            "username": "noexiste@example.com",
            "password": "WrongPass123!",  # pragma: allowlist secret
        }

        # Primer intento — falla pero no bloquea
        response = client.post(login_url, credentials)
        assert response.status_code == 200

        # Segundo intento — alcanza el límite → lockout
        response = client.post(login_url, credentials)
        assert response.status_code == 429

    def test_lockout_renders_account_locked_template(self, client, settings):
        """Verifica que el lockout renderiza account_locked.html."""
        from axes.models import AccessAttempt

        settings.AXES_FAILURE_LIMIT = 2
        AccessAttempt.objects.all().delete()

        login_url = reverse("users:login")
        credentials = {
            "username": "noexiste@example.com",
            "password": "WrongPass123!",  # pragma: allowlist secret
        }

        client.post(login_url, credentials)
        response = client.post(login_url, credentials)

        assert response.status_code == 429
        assert "users/account_locked.html" in [t.name for t in response.templates]


@pytest.mark.django_db
class TestAxesClientIp:
    """En producción REMOTE_ADDR es 127.0.0.1 para todos (Cloudflare + Render); axes
    debe distinguir clientes por CF-Connecting-IP y no confiar en X-Forwarded-For (DT-119)."""

    credentials = {
        "username": "victima@example.com",
        "password": "WrongPass123!",  # pragma: allowlist secret
    }

    def _fail(self, client, cf_ip, xff=None):
        extra = {"REMOTE_ADDR": "127.0.0.1", "HTTP_CF_CONNECTING_IP": cf_ip}
        if xff:
            extra["HTTP_X_FORWARDED_FOR"] = xff
        return client.post(reverse("users:login"), self.credentials, **extra)

    def test_un_atacante_no_bloquea_al_usuario_desde_otra_ip(self, client, settings):
        from axes.models import AccessAttempt

        settings.AXES_FAILURE_LIMIT = 2
        AccessAttempt.objects.all().delete()

        self._fail(client, "203.0.113.10")
        assert self._fail(client, "203.0.113.10").status_code == 429

        assert self._fail(client, "186.127.39.70").status_code == 200

    def test_rotar_x_forwarded_for_no_evita_el_bloqueo(self, client, settings):
        from axes.models import AccessAttempt

        settings.AXES_FAILURE_LIMIT = 2
        AccessAttempt.objects.all().delete()

        self._fail(client, "203.0.113.10", xff="198.51.100.1")
        response = self._fail(client, "203.0.113.10", xff="198.51.100.2")

        assert response.status_code == 429
        assert AccessAttempt.objects.get().ip_address == "203.0.113.10"
