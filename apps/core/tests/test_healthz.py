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

        ip = "10.0.0.1"
        cache.set(f"healthz_hits_{ip}", _HEALTHZ_LIMIT, timeout=60)

        response = client.get("/healthz/", REMOTE_ADDR=ip)

        assert response.status_code == 429

    def test_healthz_bypasses_throttle_for_render(self, client):
        """Verifica que el health checker de Render no se throttlea."""
        from config.urls import _HEALTHZ_LIMIT

        ip = "10.0.0.2"
        cache.set(f"healthz_hits_{ip}", _HEALTHZ_LIMIT + 10, timeout=60)

        response = client.get(
            "/healthz/",
            REMOTE_ADDR=ip,
            HTTP_USER_AGENT="Render/1.0",
        )

        assert response.status_code == 200

    def test_healthz_increments_cache_counter(self, client):
        """Verifica que cada request incrementa el contador en cache."""
        ip = "10.0.0.3"
        cache.delete(f"healthz_hits_{ip}")

        client.get("/healthz/", REMOTE_ADDR=ip)
        client.get("/healthz/", REMOTE_ADDR=ip)

        hits = cache.get(f"healthz_hits_{ip}", 0)
        assert hits == 2
