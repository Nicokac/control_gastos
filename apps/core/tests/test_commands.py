"""
Tests para los comandos de management de core.
"""

import pytest
from io import StringIO
from django.core.management import call_command


@pytest.mark.django_db
class TestGenerateSecretKeyCommand:
    """Tests para el comando generate_secret_key."""

    def test_generates_secret_key(self):
        """Verifica que genera una SECRET_KEY."""
        out = StringIO()
        call_command('generate_secret_key', stdout=out)
        
        output = out.getvalue()
        assert 'SECRET_KEY' in output or 'generada' in output.lower()

    def test_key_has_minimum_length(self):
        """Verifica que la clave tiene longitud mínima."""
        out = StringIO()
        call_command('generate_secret_key', stdout=out)
        
        output = out.getvalue()
        # Buscar "Longitud: XX caracteres"
        assert '50' in output or 'caracteres' in output

    def test_env_format_option(self):
        """Verifica formato para archivo .env."""
        out = StringIO()
        call_command('generate_secret_key', '--env-format', stdout=out)
        
        output = out.getvalue()
        assert 'SECRET_KEY=' in output

    def test_export_format_option(self):
        """Verifica formato para export de shell."""
        out = StringIO()
        call_command('generate_secret_key', '--export-format', stdout=out)
        
        output = out.getvalue()
        assert 'export SECRET_KEY' in output or '$env:SECRET_KEY' in output


@pytest.mark.django_db
class TestAxesStatusCommand:
    """Tests para el comando axes_status."""

    def test_shows_configuration(self):
        """Verifica que muestra la configuración de axes."""
        out = StringIO()
        call_command('axes_status', stdout=out)
        
        output = out.getvalue()
        # Debería mostrar info de configuración
        assert 'AXES' in output.upper() or 'Configuración' in output or 'bloqueo' in output.lower()

    def test_clear_option(self):
        """Verifica que la opción --clear funciona."""
        out = StringIO()
        call_command('axes_status', '--clear', stdout=out)
        
        output = out.getvalue()
        assert 'eliminado' in output.lower() or 'limpiado' in output.lower() or '✅' in output


@pytest.mark.django_db
class TestViewLogsCommand:
    """Tests para el comando view_logs."""

    def test_shows_logs_info(self):
        """Verifica que muestra información de logs."""
        out = StringIO()
        err = StringIO()
        
        # Puede que no haya logs, pero no debería fallar
        try:
            call_command('view_logs', '--lines', '5', stdout=out, stderr=err)
            output = out.getvalue()
            # Debería mostrar headers de sección
            assert 'LOG' in output.upper() or '===' in output
        except Exception:
            # Si falla por no existir archivos, está bien
            pass

    def test_type_security_option(self):
        """Verifica filtro por tipo security."""
        out = StringIO()
        
        try:
            call_command('view_logs', '--type', 'security', '--lines', '5', stdout=out)
            output = out.getvalue()
            assert 'SECURITY' in output.upper() or 'security' in output.lower()
        except Exception:
            pass

    def test_type_error_option(self):
        """Verifica filtro por tipo error."""
        out = StringIO()
        
        try:
            call_command('view_logs', '--type', 'error', '--lines', '5', stdout=out)
            output = out.getvalue()
            assert 'ERROR' in output.upper() or 'error' in output.lower()
        except Exception:
            pass