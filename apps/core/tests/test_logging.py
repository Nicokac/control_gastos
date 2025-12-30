"""
Tests para las utilidades de logging.
"""

from unittest.mock import Mock, patch

from apps.core.logging import (
    get_client_ip,
    log_login_attempt,
    log_logout,
    log_password_change,
    log_permission_denied,
    log_sensitive_action,
    log_user_registration,
)


class TestGetClientIp:
    """Tests para la función get_client_ip."""

    def test_returns_remote_addr(self):
        """Verifica que retorna REMOTE_ADDR cuando no hay proxy."""
        request = Mock()
        request.META = {"REMOTE_ADDR": "192.168.1.100"}

        ip = get_client_ip(request)

        assert ip == "192.168.1.100"

    def test_returns_x_forwarded_for(self):
        """Verifica que retorna X-Forwarded-For cuando hay proxy."""
        request = Mock()
        request.META = {
            "HTTP_X_FORWARDED_FOR": "203.0.113.195, 70.41.3.18, 150.172.238.178",
            "REMOTE_ADDR": "127.0.0.1",
        }

        ip = get_client_ip(request)

        # Debería retornar la primera IP (la del cliente original)
        assert ip == "203.0.113.195"

    def test_returns_unknown_when_no_ip(self):
        """Verifica que retorna 'unknown' cuando no hay IP."""
        request = Mock()
        request.META = {}

        ip = get_client_ip(request)

        assert ip == "unknown"

    def test_strips_whitespace_from_forwarded_ip(self):
        """Verifica que elimina espacios de la IP."""
        request = Mock()
        request.META = {
            "HTTP_X_FORWARDED_FOR": "  10.0.0.1  , 192.168.1.1",
            "REMOTE_ADDR": "127.0.0.1",
        }

        ip = get_client_ip(request)

        assert ip == "10.0.0.1"


class TestLogFunctions:
    """Tests para las funciones de logging."""

    @patch("apps.core.logging.security_logger")
    def test_log_login_attempt_success(self, mock_logger):
        """Verifica log de login exitoso."""
        log_login_attempt("user@test.com", "127.0.0.1", success=True)

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert "LOGIN" in call_args
        assert "SUCCESS" in call_args
        assert "user@test.com" in call_args
        assert "127.0.0.1" in call_args

    @patch("apps.core.logging.security_logger")
    def test_log_login_attempt_failed(self, mock_logger):
        """Verifica log de login fallido."""
        log_login_attempt("user@test.com", "127.0.0.1", success=False)

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert "LOGIN" in call_args
        assert "FAILED" in call_args

    @patch("apps.core.logging.security_logger")
    def test_log_logout(self, mock_logger):
        """Verifica log de logout."""
        log_logout("user@test.com", "192.168.1.1")

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert "LOGOUT" in call_args
        assert "user@test.com" in call_args

    @patch("apps.core.logging.security_logger")
    def test_log_password_change(self, mock_logger):
        """Verifica log de cambio de contraseña."""
        log_password_change("user@test.com", "10.0.0.1")

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert "PASSWORD_CHANGE" in call_args

    @patch("apps.core.logging.security_logger")
    def test_log_user_registration(self, mock_logger):
        """Verifica log de registro de usuario."""
        log_user_registration("newuser@test.com", "172.16.0.1")

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert "REGISTRATION" in call_args
        assert "newuser@test.com" in call_args

    @patch("apps.core.logging.security_logger")
    def test_log_permission_denied(self, mock_logger):
        """Verifica log de permiso denegado."""
        log_permission_denied("user@test.com", "127.0.0.1", "/admin/secret/")

        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]
        assert "PERMISSION_DENIED" in call_args
        assert "/admin/secret/" in call_args

    @patch("apps.core.logging.security_logger")
    def test_log_sensitive_action(self, mock_logger):
        """Verifica log de acción sensible."""
        log_sensitive_action("DELETE_USER", "admin@test.com", "127.0.0.1", "User ID: 123")

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert "DELETE_USER" in call_args
        assert "User ID: 123" in call_args

    @patch("apps.core.logging.security_logger")
    def test_log_sensitive_action_without_details(self, mock_logger):
        """Verifica log de acción sensible sin detalles."""
        log_sensitive_action("EXPORT_DATA", "user@test.com", "127.0.0.1")

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert "EXPORT_DATA" in call_args
        assert "Details" not in call_args
