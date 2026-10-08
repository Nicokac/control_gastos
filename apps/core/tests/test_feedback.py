"""
Tests para FeedbackForm y FeedbackView.
"""

from django.urls import reverse

import pytest

FEEDBACK_URL = reverse("core:feedback")


@pytest.mark.django_db
class TestFeedbackView:
    def test_no_requiere_login(self, client):
        """DT-090: alguien sin acceso a su cuenta debe poder pedir el
        borrado de datos sin loguearse, como promete account_deletion.html."""
        response = client.get(FEEDBACK_URL)
        assert response.status_code == 200

    def test_get_renders_form(self, client, user):
        client.force_login(user)
        response = client.get(FEEDBACK_URL)
        assert response.status_code == 200
        assert "form" in response.context
        assert "tipo" in response.context["form"].fields
        assert "mensaje" in response.context["form"].fields

    def test_post_valid_sends_email(self, client, user, mailoutbox):
        client.force_login(user)
        response = client.post(
            FEEDBACK_URL,
            {"tipo": "bug", "mensaje": "El gráfico no carga correctamente."},
        )
        assert response.status_code == 302
        assert len(mailoutbox) == 1
        mail = mailoutbox[0]
        assert user.username in mail.subject
        assert "Bug / Falla" in mail.subject
        assert "El gráfico no carga correctamente." in mail.body
        assert user.username in mail.body

    def test_post_invalid_tipo_shows_error(self, client, user, mailoutbox):
        client.force_login(user)
        response = client.post(
            FEEDBACK_URL,
            {"tipo": "invalido", "mensaje": "Mensaje"},
        )
        assert response.status_code == 200
        assert len(mailoutbox) == 0
        assert response.context["form"].errors

    def test_post_empty_mensaje_shows_error(self, client, user, mailoutbox):
        client.force_login(user)
        response = client.post(
            FEEDBACK_URL,
            {"tipo": "mejora", "mensaje": ""},
        )
        assert response.status_code == 200
        assert len(mailoutbox) == 0
        assert "mensaje" in response.context["form"].errors

    def test_post_mensaje_too_long_shows_error(self, client, user, mailoutbox):
        client.force_login(user)
        response = client.post(
            FEEDBACK_URL,
            {"tipo": "otro", "mensaje": "x" * 2001},
        )
        assert response.status_code == 200
        assert len(mailoutbox) == 0
        assert "mensaje" in response.context["form"].errors

    def test_success_message_shown(self, client, user, mailoutbox):
        client.force_login(user)
        response = client.post(
            FEEDBACK_URL,
            {"tipo": "pregunta", "mensaje": "¿Cómo exporto mis datos?"},
            follow=True,
        )
        messages = list(response.context["messages"])
        assert any("enviado" in str(m).lower() for m in messages)

    def test_email_send_failure_shows_error(self, client, user):
        import unittest.mock as mock

        with mock.patch("apps.core.utils.send_mail", side_effect=Exception("SMTP error")):
            client.force_login(user)
            response = client.post(
                FEEDBACK_URL,
                {"tipo": "bug", "mensaje": "Falla simulada"},
                follow=True,
            )
        messages = list(response.context["messages"])
        assert any("no se pudo" in str(m).lower() for m in messages)


@pytest.mark.django_db
class TestFeedbackViewAnonymous:
    """DT-090: feedback sin login, requiere email para identificar la cuenta."""

    def test_email_field_required_sin_login(self, client):
        response = client.get(FEEDBACK_URL)
        assert response.context["form"].fields["email"].required is True

    def test_email_field_not_required_logueado(self, client, user):
        client.force_login(user)
        response = client.get(FEEDBACK_URL)
        assert response.context["form"].fields["email"].required is False

    def test_post_sin_login_sin_email_muestra_error(self, client, mailoutbox):
        response = client.post(
            FEEDBACK_URL,
            {"tipo": "bug", "mensaje": "No puedo entrar a mi cuenta"},
        )
        assert response.status_code == 200
        assert len(mailoutbox) == 0
        assert "email" in response.context["form"].errors

    def test_post_sin_login_con_email_envia_correctamente(self, client, mailoutbox):
        response = client.post(
            FEEDBACK_URL,
            {
                "tipo": "otro",
                "email": "exusuario@example.com",
                "mensaje": "Pido eliminar mi cuenta, perdí el acceso.",
            },
        )
        assert response.status_code == 302
        assert len(mailoutbox) == 1
        mail = mailoutbox[0]
        assert "exusuario@example.com" in mail.subject
        assert "exusuario@example.com" in mail.body
        assert "Pido eliminar mi cuenta" in mail.body
