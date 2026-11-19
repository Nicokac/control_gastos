"""DT-013: los emails de registro y reset no frenan el request mientras Brevo responde."""

import threading
from unittest.mock import patch

from django.urls import reverse

import pytest


class SlowBrevo:
    """Reemplazo de send_brevo_email que no termina hasta que el test lo libera."""

    def __init__(self):
        self.release = threading.Event()
        self.done = threading.Event()
        self.calls = []

    def __call__(self, to_email, subject, body):
        self.calls.append((to_email, subject, body, threading.current_thread().name))
        self.release.wait(timeout=5)
        self.done.set()
        return True

    def finish(self):
        self.release.set()
        assert self.done.wait(timeout=5)


@pytest.fixture
def background(settings):
    settings.EMAILS_IN_BACKGROUND = True


@pytest.mark.django_db
@pytest.mark.usefixtures("background")
class TestEmailsEnSegundoPlano:
    def test_el_registro_responde_antes_de_que_brevo_termine(self, client):
        slow = SlowBrevo()
        with patch("apps.users.views.send_brevo_email", slow):
            response = client.post(
                reverse("users:register"),
                {
                    "email": "nuevo@test.com",
                    "username": "nuevousuario",
                    "password1": "TestPass123!",  # pragma: allowlist secret
                    "password2": "TestPass123!",  # pragma: allowlist secret
                    "accept_terms": True,
                },
            )
            assert response.status_code == 302
            assert not slow.done.is_set()
            slow.finish()

        to_email, subject, body, thread_name = slow.calls[0]
        assert to_email == "nuevo@test.com"
        assert subject.startswith("Verificá tu email")
        assert thread_name.startswith("email")

    def test_el_reset_web_responde_antes_de_que_brevo_termine(self, client, user):
        slow = SlowBrevo()
        with patch("apps.users.forms.send_brevo_email", slow):
            response = client.post(reverse("users:password_reset"), {"email": user.email})
            assert response.status_code == 302
            assert not slow.done.is_set()
            slow.finish()

        assert slow.calls[0][0] == user.email
        assert "/users/password/reset/" in slow.calls[0][2]

    def test_el_reset_web_usa_el_fallback_desde_el_hilo(self, client, user):
        done = threading.Event()

        def brevo_caido(*args):
            return False

        with (
            patch("apps.users.forms.send_brevo_email", brevo_caido),
            patch(
                "django.contrib.auth.forms.PasswordResetForm.send_mail",
                side_effect=lambda *a, **k: done.set(),
            ) as fallback,
        ):
            client.post(reverse("users:password_reset"), {"email": user.email})
            assert done.wait(timeout=5)

        assert fallback.call_args.args[4] == user.email

    def test_el_reset_de_la_api_responde_antes_de_que_brevo_termine(self, client, user):
        slow = SlowBrevo()
        with patch("apps.api.v1.views.auth.send_brevo_email", slow):
            response = client.post(
                "/api/v1/auth/password/reset/",
                {"email": user.email},
                content_type="application/json",
            )
            assert response.status_code == 200
            assert not slow.done.is_set()
            slow.finish()

        assert slow.calls[0][0] == user.email
