"""Tests para el endpoint de feedback de la API v1 (consumido por mobile)."""

from unittest.mock import patch

import pytest


def auth_header(client, user):
    response = client.post(
        "/api/v1/auth/token/",
        {"username": user.email, "password": "testpass123"},  # pragma: allowlist secret
        content_type="application/json",
    )
    return {"HTTP_AUTHORIZATION": f"Bearer {response.json()['access']}"}


@pytest.mark.django_db
class TestFeedbackEndpoint:
    url = "/api/v1/feedback/"

    def test_requiere_autenticacion(self, client):
        response = client.post(
            self.url,
            {"tipo": "bug", "mensaje": "Test"},
            content_type="application/json",
        )
        assert response.status_code == 401

    def test_envio_exitoso(self, client, user):
        headers = auth_header(client, user)
        with patch(
            "apps.api.v1.views.feedback.send_feedback_email", return_value=True
        ) as mock_send:
            response = client.post(
                self.url,
                {"tipo": "bug", "mensaje": "El gráfico no carga"},
                content_type="application/json",
                **headers,
            )
        assert response.status_code == 200
        mock_send.assert_called_once()
        subject, body = mock_send.call_args[0]
        assert "Bug / Falla" in subject
        assert user.username in body
        assert "El gráfico no carga" in body

    def test_incluye_contexto_tecnico_cuando_viene(self, client, user):
        headers = auth_header(client, user)
        with patch(
            "apps.api.v1.views.feedback.send_feedback_email", return_value=True
        ) as mock_send:
            response = client.post(
                self.url,
                {
                    "tipo": "bug",
                    "mensaje": "Falla al guardar",
                    "technical_context": "DioException 400: category invalida",
                },
                content_type="application/json",
                **headers,
            )
        assert response.status_code == 200
        _, body = mock_send.call_args[0]
        assert "DioException 400" in body
        assert "Contexto técnico" in body

    def test_sin_contexto_tecnico_no_agrega_seccion(self, client, user):
        headers = auth_header(client, user)
        with patch(
            "apps.api.v1.views.feedback.send_feedback_email", return_value=True
        ) as mock_send:
            client.post(
                self.url,
                {"tipo": "mejora", "mensaje": "Agregar modo oscuro"},
                content_type="application/json",
                **headers,
            )
        _, body = mock_send.call_args[0]
        assert "Contexto técnico" not in body

    def test_tipo_invalido(self, client, user):
        headers = auth_header(client, user)
        response = client.post(
            self.url,
            {"tipo": "invalido", "mensaje": "Test"},
            content_type="application/json",
            **headers,
        )
        assert response.status_code == 400

    def test_mensaje_vacio(self, client, user):
        headers = auth_header(client, user)
        response = client.post(
            self.url,
            {"tipo": "bug", "mensaje": ""},
            content_type="application/json",
            **headers,
        )
        assert response.status_code == 400

    def test_falla_el_envio_devuelve_502(self, client, user):
        headers = auth_header(client, user)
        with patch("apps.api.v1.views.feedback.send_feedback_email", return_value=False):
            response = client.post(
                self.url,
                {"tipo": "bug", "mensaje": "Test"},
                content_type="application/json",
                **headers,
            )
        assert response.status_code == 502
