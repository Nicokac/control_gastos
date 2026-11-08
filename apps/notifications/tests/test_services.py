from io import StringIO
from types import SimpleNamespace

from django.core.management import CommandError, call_command

import pytest
from firebase_admin import exceptions, messaging

from apps.notifications import services
from apps.notifications.models import DeviceToken
from apps.notifications.services import send_push_to_user


def _ok():
    return SimpleNamespace(success=True, exception=None)


def _fail(exception):
    return SimpleNamespace(success=False, exception=exception)


@pytest.fixture
def firebase_enabled(settings):
    settings.FIREBASE_CREDENTIALS_PATH = "/tmp/firebase-test.json"


@pytest.fixture
def fake_send(monkeypatch):
    """Reemplaza la llamada a Firebase; `results` define la respuesta por token, en orden."""
    state = {"messages": [], "results": None}

    def _send(message, app=None):
        state["messages"].append(message)
        results = state["results"] or [_ok() for _ in message.tokens]
        return SimpleNamespace(
            responses=results,
            success_count=sum(1 for r in results if r.success),
            failure_count=sum(1 for r in results if not r.success),
        )

    monkeypatch.setattr(services, "_get_firebase_app", lambda: None)
    monkeypatch.setattr(services.messaging, "send_each_for_multicast", _send)
    return state


@pytest.mark.django_db
class TestSendPushToUser:
    def test_sin_credenciales_no_envia(self, settings, user, fake_send):
        settings.FIREBASE_CREDENTIALS_PATH = ""
        DeviceToken.objects.create(user=user, token="fcm-1")

        assert send_push_to_user(user, "Título", "Cuerpo") == 0
        assert fake_send["messages"] == []

    def test_sin_tokens_activos_no_envia(self, firebase_enabled, user, fake_send):
        DeviceToken.objects.create(user=user, token="fcm-1", is_active=False)

        assert send_push_to_user(user, "Título", "Cuerpo") == 0
        assert fake_send["messages"] == []

    def test_envia_solo_a_tokens_activos_del_usuario(
        self, firebase_enabled, user, other_user, fake_send
    ):
        DeviceToken.objects.create(user=user, token="fcm-propio-1")
        DeviceToken.objects.create(user=user, token="fcm-propio-2")
        DeviceToken.objects.create(user=user, token="fcm-inactivo", is_active=False)
        DeviceToken.objects.create(user=other_user, token="fcm-ajeno")

        sent = send_push_to_user(user, "Título", "Cuerpo")

        assert sent == 2
        assert sorted(fake_send["messages"][0].tokens) == ["fcm-propio-1", "fcm-propio-2"]

    def test_envia_titulo_cuerpo_y_data(self, firebase_enabled, user, fake_send):
        DeviceToken.objects.create(user=user, token="fcm-1")

        send_push_to_user(user, "Vence tu alquiler", "En 3 días", data={"recurring_id": "7"})

        message = fake_send["messages"][0]
        assert message.notification.title == "Vence tu alquiler"
        assert message.notification.body == "En 3 días"
        assert message.data == {"recurring_id": "7"}

    @pytest.mark.parametrize(
        "error",
        [
            messaging.UnregisteredError("token no registrado"),
            messaging.SenderIdMismatchError("token de otro proyecto"),
        ],
    )
    def test_desactiva_tokens_invalidos(self, firebase_enabled, user, fake_send, error):
        DeviceToken.objects.create(user=user, token="fcm-valido")
        DeviceToken.objects.create(user=user, token="fcm-invalido")
        tokens = list(
            DeviceToken.objects.filter(user=user, is_active=True).values_list("token", flat=True)
        )
        fake_send["results"] = [_fail(error) if t == "fcm-invalido" else _ok() for t in tokens]

        sent = send_push_to_user(user, "Título", "Cuerpo")

        assert sent == 1
        assert DeviceToken.objects.get(token="fcm-invalido").is_active is False
        assert DeviceToken.objects.get(token="fcm-valido").is_active is True

    def test_error_transitorio_no_desactiva_token(self, firebase_enabled, user, fake_send):
        DeviceToken.objects.create(user=user, token="fcm-1")
        fake_send["results"] = [_fail(exceptions.UnavailableError("servicio caído"))]

        sent = send_push_to_user(user, "Título", "Cuerpo")

        assert sent == 0
        assert DeviceToken.objects.get(token="fcm-1").is_active is True


@pytest.mark.django_db
class TestSendTestPushCommand:
    def test_usuario_inexistente_falla(self):
        with pytest.raises(CommandError):
            call_command("send_test_push", "no-existe")

    def test_informa_cantidad_enviada(self, firebase_enabled, user, fake_send):
        DeviceToken.objects.create(user=user, token="fcm-1")
        out = StringIO()

        call_command("send_test_push", user.username, stdout=out)

        assert "Dispositivos que recibieron el push: 1" in out.getvalue()
