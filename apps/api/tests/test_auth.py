"""Tests para los endpoints de autenticación de la API v1."""

from django.contrib.auth import get_user_model

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
