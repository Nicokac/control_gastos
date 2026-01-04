"""
Tests para los formularios de users.
"""

from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory

import pytest

from apps.users.forms import LoginForm, ProfileForm, RegisterForm

User = get_user_model()


def _add_session_and_messages(request):
    """
    AuthenticationForm (y algunos flujos) pueden depender de request con session/messages.
    """
    middleware = SessionMiddleware(lambda r: None)
    middleware.process_request(request)
    request.session.save()

    # messages framework
    request._messages = FallbackStorage(request)
    return request


@pytest.fixture()
def rf():
    return RequestFactory()


@pytest.fixture()
def login_request(rf):
    request = rf.post("/login/")
    return _add_session_and_messages(request)


@pytest.fixture()
def active_user(db):
    return User.objects.create_user(
        username="nico",
        email="nico@test.com",
        password="StrongPass123!",  # pragma: allowlist secret
        is_active=True,
    )


@pytest.fixture()
def inactive_user(db):
    return User.objects.create_user(
        username="inactive",
        email="inactive@test.com",
        password="StrongPass123!",  # pragma: allowlist secret
        is_active=False,
    )


@pytest.mark.django_db
class TestLoginForm:
    def test_user_not_found_shows_specific_message(self, login_request):
        form = LoginForm(
            request=login_request,
            data={
                "username": "no-existe@test.com",
                "password": "whatever",  # pragma: allowlist secret
            },
        )
        assert not form.is_valid()
        # Tu código levanta ValidationError con este texto
        assert "Usuario o contraseña incorrectos. Verificá tus datos." in form.non_field_errors()[0]

    def test_invalid_password_shows_specific_message(self, login_request, active_user):
        form = LoginForm(
            request=login_request,
            data={
                "username": active_user.email,
                "password": "WrongPass123!",  # pragma: allowlist secret
            },
        )
        assert not form.is_valid()
        assert "Usuario o contraseña incorrectos. Verificá tus datos." in form.non_field_errors()[0]

    def test_inactive_user_shows_inactive_message(self, login_request, inactive_user):
        form = LoginForm(
            request=login_request,
            data={
                "username": inactive_user.username,
                "password": "StrongPass123!",  # pragma: allowlist secret
            },
        )
        assert not form.is_valid()
        assert "Usuario o contraseña incorrectos. Verificá tus datos." in form.non_field_errors()[0]

    def test_valid_login_by_email_succeeds(self, login_request, active_user):
        form = LoginForm(
            request=login_request,
            data={
                "username": active_user.email,
                "password": "StrongPass123!",  # pragma: allowlist secret
            },
        )
        assert form.is_valid()
        assert form.get_user() == active_user

    def test_login_trims_and_lowercases_email(self, login_request, active_user):
        form = LoginForm(
            request=login_request,
            data={
                "username": f"  {active_user.email.upper()}  ",
                "password": "StrongPass123!",  # pragma: allowlist secret
            },
        )
        assert form.is_valid()
        assert form.get_user() == active_user


@pytest.mark.django_db
class TestRegisterForm:
    def test_register_valid_user(self):
        form = RegisterForm(
            data={
                "username": "newuser",
                "email": "newuser@test.com",
                "password1": "StrongPass123!",  # pragma: allowlist secret
                "password2": "StrongPass123!",  # pragma: allowlist secret
            }
        )
        assert form.is_valid(), form.errors
        user = form.save()
        assert user.pk is not None
        assert user.username == "newuser"
        assert user.email == "newuser@test.com"  # pragma: allowlist secret

    def test_register_rejects_duplicate_email_case_insensitive(self, active_user):
        form = RegisterForm(
            data={
                "username": "another",
                "email": active_user.email.upper(),  # mismo email, distinto case
                "password1": "StrongPass123!",  # pragma: allowlist secret
                "password2": "StrongPass123!",  # pragma: allowlist secret
            }
        )
        assert not form.is_valid()
        assert "email" in form.errors
        assert "Ya existe una cuenta con este email." in form.errors["email"][0]

    def test_register_rejects_duplicate_username_case_insensitive(self, active_user):
        form = RegisterForm(
            data={
                "username": active_user.username.upper(),  # mismo username, distinto case
                "email": "other@test.com",
                "password1": "StrongPass123!",  # pragma: allowlist secret
                "password2": "StrongPass123!",  # pragma: allowlist secret
            }
        )
        assert not form.is_valid()
        assert "username" in form.errors
        assert "Este nombre de usuario ya está en uso." in form.errors["username"][0]

    def test_register_strips_username_and_normalizes_email(self):
        form = RegisterForm(
            data={
                "username": "  spaced  ",
                "email": "  MAIL@TEST.COM  ",
                "password1": "StrongPass123!",  # pragma: allowlist secret
                "password2": "StrongPass123!",  # pragma: allowlist secret
            }
        )
        assert form.is_valid(), form.errors
        user = form.save()
        # según lo que implementamos: username.strip(), email.strip().lower()
        assert user.username == "spaced"
        assert user.email == "mail@test.com"


@pytest.mark.django_db
class TestProfileForm:
    def test_profile_update_valid(self, active_user):
        form = ProfileForm(
            instance=active_user,
            data={
                "first_name": "Nico",
                "last_name": "K",
                "email": "nico_new@test.com",
                "default_currency": getattr(active_user, "default_currency", "ARS"),
                "alert_threshold": 80,
            },
        )
        assert form.is_valid(), form.errors
        user = form.save()
        assert user.email == "nico_new@test.com"

    def test_profile_rejects_email_used_by_other_user_case_insensitive(self, active_user):
        other = User.objects.create_user(
            username="other",
            email="other@test.com",
            password="StrongPass123!",  # pragma: allowlist secret
            is_active=True,
        )

        form = ProfileForm(
            instance=active_user,
            data={
                "first_name": active_user.first_name,
                "last_name": active_user.last_name,
                "email": other.email.upper(),  # mismo email de otro user
                "default_currency": getattr(active_user, "default_currency", "ARS"),
                "alert_threshold": 80,
            },
        )

        assert not form.is_valid()
        assert "email" in form.errors
        assert "Este mail ya está en uso por otra cuenta." in form.errors["email"][0]

    @pytest.mark.parametrize("bad_value", [0, 101, -5])
    def test_profile_alert_threshold_out_of_range_invalid(self, active_user, bad_value):
        form = ProfileForm(
            instance=active_user,
            data={
                "first_name": active_user.first_name,
                "last_name": active_user.last_name,
                "email": active_user.email,
                "default_currency": getattr(active_user, "default_currency", "ARS"),
                "alert_threshold": bad_value,
            },
        )
        assert not form.is_valid()
        assert "alert_threshold" in form.errors
