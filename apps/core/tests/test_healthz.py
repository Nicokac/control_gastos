from unittest.mock import patch

from django.db.utils import OperationalError

import pytest


@pytest.mark.django_db
class TestHealthz:
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
