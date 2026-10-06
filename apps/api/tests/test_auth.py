"""Tests para los endpoints de autenticación de la API v1."""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

import pytest

User = get_user_model()


@pytest.mark.django_db
class TestRegisterEndpoint:
    url = "/api/v1/auth/register/"

    def test_registro_exitoso(self, client):
        data = {
            "email": "nuevo@test.com",
            "username": "nuevousuario",
            "password": "TestPass123!",  # pragma: allowlist secret  # pragma: allowlist secret
            "password2": "TestPass123!",  # pragma: allowlist secret  # pragma: allowlist secret
        }
        response = client.post(self.url, data, content_type="application/json")
        assert response.status_code == 201
        assert User.objects.filter(email="nuevo@test.com").exists()

    def test_email_duplicado(self, client, user):
        data = {
            "email": user.email,
            "username": "otrousuario",
            "password": "TestPass123!",  # pragma: allowlist secret
            "password2": "TestPass123!",  # pragma: allowlist secret
        }
        response = client.post(self.url, data, content_type="application/json")
        assert response.status_code == 400
        assert "email" in response.json()

    def test_passwords_no_coinciden(self, client):
        data = {
            "email": "test@test.com",
            "username": "testuser",
            "password": "TestPass123!",  # pragma: allowlist secret
            "password2": "Diferente123!",  # pragma: allowlist secret
        }
        response = client.post(self.url, data, content_type="application/json")
        assert response.status_code == 400

    def test_username_duplicado(self, client, user):
        data = {
            "email": "otro@test.com",
            "username": user.username,
            "password": "TestPass123!",  # pragma: allowlist secret
            "password2": "TestPass123!",  # pragma: allowlist secret
        }
        response = client.post(self.url, data, content_type="application/json")
        assert response.status_code == 400
        assert "username" in response.json()


@pytest.mark.django_db
class TestTokenEndpoint:
    url = "/api/v1/auth/token/"

    def test_token_con_credenciales_validas(self, client, user):
        response = client.post(
            self.url,
            {"username": user.email, "password": "testpass123"},  # pragma: allowlist secret
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert "access" in data
        assert "refresh" in data

    def test_token_con_credenciales_invalidas(self, client):
        response = client.post(
            self.url,
            {"username": "noexiste@test.com", "password": "wrongpass"},  # pragma: allowlist secret
            content_type="application/json",
        )
        assert response.status_code == 401

    def test_refresh_token(self, client, user):
        token_response = client.post(
            self.url,
            {"username": user.email, "password": "testpass123"},  # pragma: allowlist secret
            content_type="application/json",
        )
        refresh = token_response.json()["refresh"]
        response = client.post(
            "/api/v1/auth/token/refresh/",
            {"refresh": refresh},
            content_type="application/json",
        )
        assert response.status_code == 200
        assert "access" in response.json()


@pytest.mark.django_db
class TestPasswordResetRequestEndpoint:
    url = "/api/v1/auth/password/reset/"

    def test_email_existente_envia_correo(self, client, user):
        with patch("apps.api.v1.views.auth.send_brevo_email", return_value=True) as mock_send:
            response = client.post(self.url, {"email": user.email}, content_type="application/json")
        assert response.status_code == 200
        mock_send.assert_called_once()
        assert mock_send.call_args[0][0] == user.email

    def test_email_inexistente_no_revela_la_cuenta(self, client):
        """Mismo 200 que con un email existente — evita enumeración de cuentas."""
        with patch("apps.api.v1.views.auth.send_brevo_email") as mock_send:
            response = client.post(
                self.url, {"email": "noexiste@test.com"}, content_type="application/json"
            )
        assert response.status_code == 200
        mock_send.assert_not_called()

    def test_email_invalido(self, client):
        response = client.post(
            self.url, {"email": "no-es-un-email"}, content_type="application/json"
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestPasswordResetConfirmEndpoint:
    url = "/api/v1/auth/password/reset/confirm/"

    def _valid_payload(self, user, **overrides):
        payload = {
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": default_token_generator.make_token(user),
            "new_password": "NuevaPass123!",  # pragma: allowlist secret
            "new_password2": "NuevaPass123!",  # pragma: allowlist secret
        }
        payload.update(overrides)
        return payload

    def test_confirma_y_cambia_la_password(self, client, user):
        response = client.post(self.url, self._valid_payload(user), content_type="application/json")
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.check_password("NuevaPass123!")

    def test_token_invalido(self, client, user):
        payload = self._valid_payload(user, token="token-invalido")
        response = client.post(self.url, payload, content_type="application/json")
        assert response.status_code == 400

    def test_uid_invalido(self, client, user):
        payload = self._valid_payload(user, uid="uid-invalido")
        response = client.post(self.url, payload, content_type="application/json")
        assert response.status_code == 400

    def test_passwords_no_coinciden(self, client, user):
        payload = self._valid_payload(user, new_password2="Diferente123!")
        response = client.post(self.url, payload, content_type="application/json")
        assert response.status_code == 400

    def test_token_no_reutilizable(self, client, user):
        """El token queda invalidado tras cambiar la password, por el hash
        de la password en PasswordResetTokenGenerator."""
        payload = self._valid_payload(user)
        first = client.post(self.url, payload, content_type="application/json")
        assert first.status_code == 200

        second = client.post(self.url, payload, content_type="application/json")
        assert second.status_code == 400


@pytest.mark.django_db
class TestMeEndpoint:
    url = "/api/v1/auth/me/"

    def _get_token(self, client, user):
        response = client.post(
            "/api/v1/auth/token/",
            {"username": user.email, "password": "testpass123"},  # pragma: allowlist secret
            content_type="application/json",
        )
        return response.json()["access"]

    def test_get_perfil_autenticado(self, client, user):
        token = self._get_token(client, user)
        response = client.get(self.url, HTTP_AUTHORIZATION=f"Bearer {token}")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user.email
        assert "id" in data

    def test_get_perfil_sin_autenticar(self, client):
        response = client.get(self.url)
        assert response.status_code == 401

    def test_actualizar_perfil(self, client, user):
        token = self._get_token(client, user)
        response = client.put(
            self.url,
            {"first_name": "Nicolás"},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.first_name == "Nicolás"
