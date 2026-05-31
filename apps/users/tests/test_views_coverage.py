"""Tests adicionales de cobertura para users/views.py."""

from unittest.mock import patch

from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

import pytest

from apps.users.models import User
from apps.users.tokens import email_verification_token


@pytest.mark.django_db
class TestCustomLogoutViewGet:
    """Línea 95: GET a logout está deshabilitado — devuelve 405."""

    def test_get_logout_returns_405(self, authenticated_client):
        url = reverse("users:logout")
        response = authenticated_client.get(url)
        assert response.status_code == 405


@pytest.mark.django_db
class TestCustomLogoutViewDispatch:
    """Líneas 98-102: dispatch loggea y agrega mensaje cuando usuario está autenticado."""

    def test_logout_adds_info_message(self, client, user):
        client.force_login(user)
        url = reverse("users:logout")
        response = client.post(url, follow=True)
        msgs = [m.message for m in response.context["messages"]]
        assert any("Sesión cerrada" in m for m in msgs)

    def test_anonymous_logout_does_not_crash(self, client):
        url = reverse("users:logout")
        response = client.post(url)
        assert response.status_code == 302


@pytest.mark.django_db
class TestVerifyEmailView:
    """Líneas 207-225: verificación de email."""

    def _make_verify_url(self, user):
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = email_verification_token.make_token(user)
        return reverse("users:verify_email", kwargs={"uidb64": uid, "token": token})

    def test_valid_token_verifies_email(self, client):
        user = User.objects.create_user(
            email="verify@test.com",
            username="verifyuser",
            password="Pass123!",  # pragma: allowlist secret
        )
        assert not user.email_verified

        url = self._make_verify_url(user)
        with patch("apps.users.views.send_brevo_email"):
            response = client.get(url, follow=True)

        user.refresh_from_db()
        assert user.email_verified
        msgs = [m.message for m in response.context["messages"]]
        assert any("verificado" in m for m in msgs)

    def test_already_verified_shows_info_message(self, client):
        user = User.objects.create_user(
            email="already@test.com",
            username="alreadyverified",
            password="Pass123!",  # pragma: allowlist secret
            email_verified=True,
        )
        url = self._make_verify_url(user)
        response = client.get(url, follow=True)
        msgs = [m.message for m in response.context["messages"]]
        assert any("ya estaba verificado" in m for m in msgs)

    def test_invalid_token_shows_error_message(self, client):
        url = reverse("users:verify_email", kwargs={"uidb64": "invalid", "token": "invalid"})
        response = client.get(url, follow=True)
        msgs = [m.message for m in response.context["messages"]]
        assert any("inválido" in m for m in msgs)

    def test_valid_token_authenticated_user_redirects_to_dashboard(self, client, user):
        user.email_verified = False
        user.save()
        client.force_login(user)
        url = self._make_verify_url(user)
        with patch("apps.users.views.send_brevo_email"):
            response = client.get(url)
        assert response.status_code == 302
        assert "dashboard" in response["Location"]

    def test_valid_token_unauthenticated_redirects_to_login(self, client):
        user = User.objects.create_user(
            email="unauth@test.com",
            username="unauthverify",
            password="Pass123!",  # pragma: allowlist secret
        )
        url = self._make_verify_url(user)
        with patch("apps.users.views.send_brevo_email"):
            response = client.get(url)
        assert response.status_code == 302
        assert "login" in response["Location"]


@pytest.mark.django_db
class TestTourDoneView:
    """Líneas 230-232: TourDoneView."""

    def test_tour_done_marks_user(self, authenticated_client, user):
        user.has_seen_tour = False
        user.save()
        url = reverse("users:tour_done")
        response = authenticated_client.post(url)
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.has_seen_tour is True

    def test_tour_done_returns_json_ok(self, authenticated_client):
        import json

        url = reverse("users:tour_done")
        response = authenticated_client.post(url)
        data = json.loads(response.content)
        assert data == {"ok": True}

    def test_tour_done_requires_login(self, client):
        url = reverse("users:tour_done")
        response = client.post(url)
        assert response.status_code == 302


@pytest.mark.django_db
class TestTourResetView:
    """Líneas 236-239: TourResetView."""

    def test_tour_reset_resets_flag(self, authenticated_client, user):
        user.has_seen_tour = True
        user.save()
        url = reverse("users:tour_reset")
        authenticated_client.post(url)
        user.refresh_from_db()
        assert user.has_seen_tour is False

    def test_tour_reset_redirects_to_dashboard(self, authenticated_client):
        url = reverse("users:tour_reset")
        response = authenticated_client.post(url)
        assert response.status_code == 302
        assert "dashboard" in response["Location"]

    def test_tour_reset_requires_login(self, client):
        url = reverse("users:tour_reset")
        response = client.post(url)
        assert response.status_code == 302


@pytest.mark.django_db
class TestResendVerificationView:
    """Líneas 243-248: ResendVerificationView."""

    def test_resend_when_already_verified_shows_info(self, client, user):
        user.email_verified = True
        user.save()
        client.force_login(user)
        url = reverse("users:resend_verification")
        response = client.get(url, follow=True)
        msgs = [m.message for m in response.context["messages"]]
        assert any("ya está verificado" in m for m in msgs)

    def test_resend_when_not_verified_sends_email(self, client, user):
        user.email_verified = False
        user.save()
        client.force_login(user)
        url = reverse("users:resend_verification")
        with patch("apps.users.views.send_brevo_email") as mock_send:
            response = client.get(url, follow=True)
        mock_send.assert_called_once()
        msgs = [m.message for m in response.context["messages"]]
        assert any("reenviamos" in m for m in msgs)

    def test_resend_requires_login(self, client):
        url = reverse("users:resend_verification")
        response = client.get(url)
        assert response.status_code == 302


@pytest.mark.django_db
class TestBrevoPasswordResetView:
    """Líneas 191-202: send_mail via Brevo con fallback a SMTP."""

    def test_password_reset_page_renders(self, client):
        url = reverse("users:password_reset")
        response = client.get(url)
        assert response.status_code == 200

    def test_password_reset_send_mail_uses_brevo_when_succeeds(self):
        from apps.users.views import BrevoPasswordResetView

        view = BrevoPasswordResetView()
        context = {}
        with (
            patch("apps.users.views.render_to_string", return_value="body"),
            patch("apps.users.views.send_brevo_email", return_value=True) as mock_send,
        ):
            view.send_mail(
                "users/emails/password_reset_subject.txt",
                "users/emails/password_reset.txt",
                context,
                from_email=None,
                to_email="dest@test.com",
            )
        mock_send.assert_called_once()

    def test_password_reset_send_mail_falls_back_to_smtp_when_brevo_fails(self):
        from apps.users.views import BrevoPasswordResetView

        view = BrevoPasswordResetView()
        context = {}
        with (
            patch("apps.users.views.render_to_string", return_value="body"),
            patch("apps.users.views.send_brevo_email", return_value=False),
            patch(
                "django.contrib.auth.views.PasswordResetView.send_mail",
                create=True,
                return_value=None,
            ) as mock_smtp,
        ):
            view.send_mail(
                "users/emails/password_reset_subject.txt",
                "users/emails/password_reset.txt",
                context,
                from_email=None,
                to_email="dest@test.com",
            )
        mock_smtp.assert_called_once()
