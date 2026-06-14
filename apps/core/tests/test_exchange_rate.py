import json
from unittest.mock import MagicMock, patch

from django.core.cache import cache

import pytest


@pytest.mark.django_db
class TestExchangeRateToday:
    URL = "/api/exchange-rate/"

    def setup_method(self):
        cache.clear()

    def _make_api_response(self, venta=1450, fecha="2026-06-13T14:30:00.000Z"):
        payload = json.dumps({"venta": venta, "fechaActualizacion": fecha}).encode()
        mock_resp = MagicMock()
        mock_resp.read.return_value = payload
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    def _login(self, client, django_user_model, username="u"):
        user = django_user_model.objects.create_user(username=username, password="p")
        client.force_login(user)
        return user

    def test_requiere_login(self, client):
        response = client.get(self.URL)
        assert response.status_code == 302

    @patch("apps.core.views.urllib.request.urlopen")
    def test_devuelve_venta_y_updated_at(self, mock_urlopen, client, django_user_model):
        self._login(client, django_user_model, "u1")
        mock_urlopen.return_value = self._make_api_response()

        response = client.get(self.URL)

        assert response.status_code == 200
        data = response.json()
        assert data["venta"] == "1450"
        assert data["updated_at"] == "2026-06-13T14:30:00.000Z"

    @patch("apps.core.views.urllib.request.urlopen")
    def test_envia_user_agent(self, mock_urlopen, client, django_user_model):
        self._login(client, django_user_model, "u2")
        mock_urlopen.return_value = self._make_api_response()

        client.get(self.URL)

        args, _ = mock_urlopen.call_args
        req = args[0]
        assert req.get_header("User-agent") == "Mozilla/5.0"

    @patch("apps.core.views.urllib.request.urlopen")
    def test_usa_cache_en_segundo_request(self, mock_urlopen, client, django_user_model):
        self._login(client, django_user_model, "u3")
        mock_urlopen.return_value = self._make_api_response()

        client.get(self.URL)
        client.get(self.URL)

        assert mock_urlopen.call_count == 1

    @patch("apps.core.views.urllib.request.urlopen")
    def test_devuelve_503_si_api_falla(self, mock_urlopen, client, django_user_model):
        self._login(client, django_user_model, "u4")
        mock_urlopen.side_effect = Exception("timeout")

        response = client.get(self.URL)

        assert response.status_code == 503
        assert "error" in response.json()

    @patch("apps.core.views.urllib.request.urlopen")
    def test_cache_no_llama_api_segunda_vez(self, mock_urlopen, client, django_user_model):
        self._login(client, django_user_model, "u5")
        mock_urlopen.return_value = self._make_api_response(venta=1450)

        r1 = client.get(self.URL)
        r2 = client.get(self.URL)

        assert r1.json()["venta"] == r2.json()["venta"]
        assert mock_urlopen.call_count == 1
