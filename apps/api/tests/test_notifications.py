"""Tests para el endpoint de registro de token de dispositivo (push, mobile)."""

import pytest

from apps.notifications.models import DeviceToken


def auth_header(client, user):
    response = client.post(
        "/api/v1/auth/token/",
        {"username": user.email, "password": "testpass123"},  # pragma: allowlist secret
        content_type="application/json",
    )
    return {"HTTP_AUTHORIZATION": f"Bearer {response.json()['access']}"}


@pytest.mark.django_db
class TestDeviceTokenRegisterEndpoint:
    url = "/api/v1/notifications/device-token/"

    def test_requiere_autenticacion(self, client):
        response = client.post(self.url, {"token": "abc123"}, content_type="application/json")
        assert response.status_code == 401

    def test_registra_token_nuevo(self, client, user):
        headers = auth_header(client, user)
        response = client.post(
            self.url,
            {"token": "fcm-token-nuevo", "platform": "ANDROID"},
            content_type="application/json",
            **headers,
        )
        assert response.status_code == 204
        device = DeviceToken.objects.get(token="fcm-token-nuevo")
        assert device.user == user
        assert device.platform == "ANDROID"
        assert device.is_active is True

    def test_platform_por_defecto_es_android(self, client, user):
        headers = auth_header(client, user)
        response = client.post(
            self.url,
            {"token": "fcm-token-sin-platform"},
            content_type="application/json",
            **headers,
        )
        assert response.status_code == 204
        device = DeviceToken.objects.get(token="fcm-token-sin-platform")
        assert device.platform == "ANDROID"

    def test_registrar_token_existente_lo_actualiza_sin_duplicar(self, client, user, other_user):
        """Firebase puede reasignar el mismo token a otro usuario (instalación
        anterior desinstalada) — no debe fallar, debe reasignarlo."""
        DeviceToken.objects.create(user=other_user, token="fcm-token-compartido")

        headers = auth_header(client, user)
        response = client.post(
            self.url,
            {"token": "fcm-token-compartido", "platform": "ANDROID"},
            content_type="application/json",
            **headers,
        )

        assert response.status_code == 204
        assert DeviceToken.objects.filter(token="fcm-token-compartido").count() == 1
        device = DeviceToken.objects.get(token="fcm-token-compartido")
        assert device.user == user

    def test_reregistrar_token_inactivo_lo_reactiva(self, client, user):
        device = DeviceToken.objects.create(user=user, token="fcm-token-viejo", is_active=False)

        headers = auth_header(client, user)
        client.post(
            self.url,
            {"token": "fcm-token-viejo", "platform": "ANDROID"},
            content_type="application/json",
            **headers,
        )

        device.refresh_from_db()
        assert device.is_active is True

    def test_token_faltante_devuelve_400(self, client, user):
        headers = auth_header(client, user)
        response = client.post(self.url, {}, content_type="application/json", **headers)
        assert response.status_code == 400


@pytest.mark.django_db
class TestDeviceTokenUnregisterEndpoint:
    url = "/api/v1/notifications/device-token/"

    def test_requiere_autenticacion(self, client):
        response = client.delete(self.url, {"token": "abc123"}, content_type="application/json")
        assert response.status_code == 401

    def test_desactiva_el_token_propio(self, client, user):
        DeviceToken.objects.create(user=user, token="fcm-token-a-borrar")
        headers = auth_header(client, user)

        response = client.delete(
            self.url,
            {"token": "fcm-token-a-borrar"},
            content_type="application/json",
            **headers,
        )

        assert response.status_code == 204
        device = DeviceToken.objects.get(token="fcm-token-a-borrar")
        assert device.is_active is False

    def test_no_puede_desactivar_token_ajeno(self, client, user, other_user):
        DeviceToken.objects.create(user=other_user, token="fcm-token-ajeno")
        headers = auth_header(client, user)

        client.delete(
            self.url,
            {"token": "fcm-token-ajeno"},
            content_type="application/json",
            **headers,
        )

        device = DeviceToken.objects.get(token="fcm-token-ajeno")
        assert device.is_active is True  # sin cambios, no era del usuario autenticado

    def test_sin_token_devuelve_400(self, client, user):
        headers = auth_header(client, user)
        response = client.delete(self.url, {}, content_type="application/json", **headers)
        assert response.status_code == 400
