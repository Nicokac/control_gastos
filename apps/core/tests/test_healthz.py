from unittest.mock import patch

from django.core.cache import cache
from django.db.utils import OperationalError

import pytest


@pytest.mark.django_db
class TestHealthz:
    def setup_method(self):
        cache.clear()

    def test_healthz_returns_200_when_db_is_available(self, client):
        response = client.get("/healthz/")

        assert response.status_code == 200
        assert response.content.decode() == "ok"

    @patch("django.db.connection.ensure_connection")
    def test_healthz_returns_503_when_db_fails(self, mock_ensure_connection, client):
        mock_ensure_connection.side_effect = OperationalError("db down")

        response = client.get("/healthz/")

        assert response.status_code == 503
        assert "error:" in response.content.decode()

    def test_healthz_throttles_after_limit(self, client):
        """Verifica que devuelve 429 al superar el límite de requests."""
        from config.urls import _HEALTHZ_LIMIT

        ip = "203.0.113.1"
        cache.set(f"healthz_hits_{ip}", _HEALTHZ_LIMIT, timeout=60)

        response = client.get("/healthz/", HTTP_CF_CONNECTING_IP=ip)

        assert response.status_code == 429

    def test_healthz_increments_cache_counter(self, client):
        """Verifica que cada request incrementa el contador en cache."""
        ip = "203.0.113.3"

        client.get("/healthz/", HTTP_CF_CONNECTING_IP=ip)
        client.get("/healthz/", HTTP_CF_CONNECTING_IP=ip)

        assert cache.get(f"healthz_hits_{ip}", 0) == 2


@pytest.mark.django_db
class TestHealthzRenderBypass:
    def setup_method(self):
        cache.clear()

    def test_health_check_interno_no_se_throttlea(self, client):
        from config.urls import _HEALTHZ_LIMIT

        ip = "127.0.0.1"
        cache.set(f"healthz_hits_{ip}", _HEALTHZ_LIMIT + 10, timeout=60)

        response = client.get("/healthz/", REMOTE_ADDR=ip, HTTP_USER_AGENT="Render/1.0")

        assert response.status_code == 200

    def test_health_check_interno_no_suma_al_contador(self, client):
        client.get("/healthz/", REMOTE_ADDR="127.0.0.1")

        assert cache.get("healthz_hits_127.0.0.1") is None

    def test_user_agent_render_desde_internet_se_throttlea(self, client):
        from config.urls import _HEALTHZ_LIMIT

        ip = "203.0.113.2"
        cache.set(f"healthz_hits_{ip}", _HEALTHZ_LIMIT, timeout=60)

        response = client.get(
            "/healthz/",
            REMOTE_ADDR="127.0.0.1",
            HTTP_CF_CONNECTING_IP=ip,
            HTTP_USER_AGENT="Render/1.0",
        )

        assert response.status_code == 429


@pytest.mark.django_db
class TestHealthzClientIp:
    def setup_method(self):
        cache.clear()

    def test_rotar_x_forwarded_for_no_evita_el_limite(self, client):
        from config.urls import _HEALTHZ_LIMIT

        ip = "203.0.113.20"
        cache.set(f"healthz_hits_{ip}", _HEALTHZ_LIMIT, timeout=60)

        response = client.get(
            "/healthz/",
            REMOTE_ADDR="127.0.0.1",
            HTTP_CF_CONNECTING_IP=ip,
            HTTP_X_FORWARDED_FOR="198.51.100.9",
        )

        assert response.status_code == 429
