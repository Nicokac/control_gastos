"""Tests para el endpoint de registro de token de dispositivo (push, mobile)."""

from datetime import timedelta

from django.utils import timezone

import pytest

from apps.notifications.models import DeviceToken, Notification


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


@pytest.mark.django_db
class TestRecurringRemindersCronEndpoint:
    url = "/api/v1/notifications/cron/recurring-reminders/"
    secret = "cron-secret-de-prueba"  # pragma: allowlist secret

    @pytest.fixture
    def sent_calls(self, monkeypatch):
        calls = []

        def fake_send():
            calls.append(True)
            return 2

        monkeypatch.setattr("apps.api.v1.views.notifications.send_recurring_reminders", fake_send)
        monkeypatch.setattr("apps.api.v1.views.notifications.check_brevo_account", lambda: True)
        return calls

    def test_con_secreto_correcto_envia_y_devuelve_cantidad(self, client, settings, sent_calls):
        settings.CRON_SECRET = self.secret
        response = client.post(self.url, HTTP_X_CRON_SECRET=self.secret)
        assert response.status_code == 200
        assert response.json() == {"sent": 2, "brevo_ok": True}
        assert len(sent_calls) == 1

    def test_informa_si_la_key_de_brevo_falla(self, client, settings, sent_calls, monkeypatch):
        settings.CRON_SECRET = self.secret
        monkeypatch.setattr("apps.api.v1.views.notifications.check_brevo_account", lambda: False)
        response = client.post(self.url, HTTP_X_CRON_SECRET=self.secret)
        assert response.status_code == 200
        assert response.json() == {"sent": 2, "brevo_ok": False}

    def test_secreto_incorrecto_responde_403_sin_enviar(self, client, settings, sent_calls):
        settings.CRON_SECRET = self.secret
        response = client.post(self.url, HTTP_X_CRON_SECRET="otro")
        assert response.status_code == 403
        assert sent_calls == []

    def test_sin_header_responde_403(self, client, settings, sent_calls):
        settings.CRON_SECRET = self.secret
        response = client.post(self.url)
        assert response.status_code == 403
        assert sent_calls == []

    def test_sin_secreto_configurado_queda_desactivado(self, client, settings, sent_calls):
        settings.CRON_SECRET = ""
        response = client.post(self.url, HTTP_X_CRON_SECRET="")
        assert response.status_code == 403
        assert sent_calls == []

    def test_un_jwt_de_usuario_no_alcanza(self, client, settings, user, sent_calls):
        settings.CRON_SECRET = self.secret
        response = client.post(self.url, **auth_header(client, user))
        assert response.status_code == 403
        assert sent_calls == []

    def test_get_no_permitido(self, client, settings, sent_calls):
        settings.CRON_SECRET = self.secret
        response = client.get(self.url, HTTP_X_CRON_SECRET=self.secret)
        assert response.status_code == 405
        assert sent_calls == []

    def test_integracion_sin_dispositivos_no_envia_nada(self, client, settings):
        settings.CRON_SECRET = self.secret
        settings.BREVO_API_KEY = ""
        response = client.post(self.url, HTTP_X_CRON_SECRET=self.secret)
        assert response.status_code == 200
        assert response.json() == {"sent": 0, "brevo_ok": False}


@pytest.fixture
def make_notification(user):
    def _make(owner=None, body="En 3 días vence Alquiler.", read_at=None):
        return Notification.objects.create(
            user=owner or user,
            type="recurring_reminder",
            title="Gastos fijos por vencer",
            body=body,
            read_at=read_at,
        )

    return _make


@pytest.mark.django_db
class TestNotificationListEndpoint:
    url = "/api/v1/notifications/"

    def test_requiere_autenticacion(self, client):
        assert client.get(self.url).status_code == 401

    def test_lista_solo_las_del_usuario_mas_recientes_primero(
        self, client, user, other_user, make_notification
    ):
        vieja = make_notification(body="vieja")
        nueva = make_notification(body="nueva")
        make_notification(owner=other_user, body="ajena")

        response = client.get(self.url, **auth_header(client, user))

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert [n["id"] for n in data["results"]] == [nueva.id, vieja.id]
        assert set(data["results"][0]) == {"id", "type", "title", "body", "created_at", "read_at"}

    def test_sin_avisos_devuelve_lista_vacia(self, client, user):
        response = client.get(self.url, **auth_header(client, user))
        assert response.json()["results"] == []

    def test_cantidad_de_queries_no_crece_con_los_avisos(
        self, client, user, make_notification, django_assert_max_num_queries
    ):
        headers = auth_header(client, user)
        for i in range(10):
            make_notification(body=f"aviso {i}")
        with django_assert_max_num_queries(4):
            client.get(self.url, **headers)


@pytest.mark.django_db
class TestNotificationUnreadCountEndpoint:
    url = "/api/v1/notifications/unread-count/"

    def test_requiere_autenticacion(self, client):
        assert client.get(self.url).status_code == 401

    def test_cuenta_solo_las_no_leidas_del_usuario(
        self, client, user, other_user, make_notification
    ):
        make_notification()
        make_notification()
        make_notification(read_at=timezone.now())
        make_notification(owner=other_user)

        response = client.get(self.url, **auth_header(client, user))

        assert response.status_code == 200
        assert response.json() == {"unread": 2}


@pytest.mark.django_db
class TestNotificationMarkReadEndpoint:
    url = "/api/v1/notifications/mark-read/"

    def test_requiere_autenticacion(self, client):
        assert client.post(self.url).status_code == 401

    def test_marca_leidas_las_del_usuario_sin_tocar_las_ajenas(
        self, client, user, other_user, make_notification
    ):
        propia = make_notification()
        ajena = make_notification(owner=other_user)

        response = client.post(self.url, **auth_header(client, user))

        assert response.status_code == 204
        propia.refresh_from_db()
        ajena.refresh_from_db()
        assert propia.read_at is not None
        assert ajena.read_at is None

    def test_no_pisa_la_fecha_de_las_ya_leidas(self, client, user, make_notification):
        leida_antes = timezone.now() - timedelta(days=5)
        notification = make_notification(read_at=leida_antes)

        client.post(self.url, **auth_header(client, user))

        notification.refresh_from_db()
        assert notification.read_at == leida_antes


@pytest.mark.django_db
class TestRecurringRemindersPreference:
    url = "/api/v1/auth/me/"

    def test_por_defecto_estan_activados(self, client, user):
        response = client.get(self.url, **auth_header(client, user))
        assert response.json()["recurring_reminders_enabled"] is True

    def test_se_pueden_desactivar_desde_el_perfil(self, client, user):
        response = client.put(
            self.url,
            {"recurring_reminders_enabled": False},
            content_type="application/json",
            **auth_header(client, user),
        )

        assert response.status_code == 200
        assert response.json()["recurring_reminders_enabled"] is False
        user.refresh_from_db()
        assert user.recurring_reminders_enabled is False

    def test_alertas_de_gastos_se_pueden_desactivar_desde_el_perfil(self, client, user):
        headers = auth_header(client, user)
        assert client.get(self.url, **headers).json()["spending_alerts_enabled"] is True

        response = client.put(
            self.url,
            {"spending_alerts_enabled": False},
            content_type="application/json",
            **headers,
        )

        assert response.json()["spending_alerts_enabled"] is False
        user.refresh_from_db()
        assert user.spending_alerts_enabled is False
