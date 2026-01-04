"""
Tests para apps.users.backends.EmailOrUsernameModelBackend
"""

from django.contrib.auth import get_user_model

import pytest

from apps.users.backends import EmailOrUsernameModelBackend

User = get_user_model()


@pytest.mark.django_db
class TestEmailOrUsernameModelBackend:
    def test_authenticate_with_username_success(self):
        user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="TestPass123!",  # pragma: allowlist secret
        )

        backend = EmailOrUsernameModelBackend()
        result = backend.authenticate(request=None, username="testuser", password="TestPass123!")

        assert result == user

    def test_authenticate_with_email_success(self):
        user = User.objects.create_user(
            username="testuser2",
            email="testuser2@example.com",
            password="TestPass123!",  # pragma: allowlist secret
        )

        backend = EmailOrUsernameModelBackend()
        result = backend.authenticate(
            request=None,
            username="testuser2@example.com",
            password="TestPass123!",  # pragma: allowlist secret
        )

        assert result == user

    def test_authenticate_is_case_insensitive_for_username_and_email(self):
        user = User.objects.create_user(
            username="CaseUser",
            email="CaseUser@Example.com",
            password="TestPass123!",  # pragma: allowlist secret
        )

        backend = EmailOrUsernameModelBackend()

        # username__iexact
        result_username = backend.authenticate(
            request=None,
            username="caseuser",
            password="TestPass123!",  # pragma: allowlist secret
        )
        assert result_username == user

        # email__iexact
        result_email = backend.authenticate(
            request=None,
            username="caseuser@example.com",
            password="TestPass123!",  # pragma: allowlist secret
        )
        assert result_email == user

    def test_authenticate_returns_none_if_password_is_none(self):
        User.objects.create_user(
            username="testuser3",
            email="testuser3@example.com",
            password="TestPass123!",  # pragma: allowlist secret
        )
        backend = EmailOrUsernameModelBackend()

        result = backend.authenticate(request=None, username="testuser3", password=None)
        assert result is None

    def test_authenticate_returns_none_if_username_is_none_even_with_kwargs(self):
        backend = EmailOrUsernameModelBackend()
        result = backend.authenticate(request=None, username=None, password="TestPass123!")
        assert result is None

    def test_authenticate_returns_none_if_user_not_found(self):
        backend = EmailOrUsernameModelBackend()
        result = backend.authenticate(
            request=None,
            username="doesnotexist",
            password="TestPass123!",  # pragma: allowlist secret
        )
        assert result is None

    def test_authenticate_returns_none_if_password_incorrect(self):
        User.objects.create_user(
            username="wrongpass",
            email="wrongpass@example.com",
            password="CorrectPass123!",  # pragma: allowlist secret
        )
        backend = EmailOrUsernameModelBackend()

        result = backend.authenticate(
            request=None,
            username="wrongpass",
            password="BadPass123!",  # pragma: allowlist secret
        )
        assert result is None

    def test_authenticate_returns_none_if_user_inactive(self):
        """
        Cobertura del branch user_can_authenticate(user) == False
        """
        user = User.objects.create_user(
            username="inactiveuser",
            email="inactive@example.com",
            password="TestPass123!",  # pragma: allowlist secret
        )
        user.is_active = False
        user.save(update_fields=["is_active"])

        backend = EmailOrUsernameModelBackend()
        result = backend.authenticate(
            request=None,
            username="inactiveuser",
            password="TestPass123!",  # pragma: allowlist secret
        )

        assert result is None

    def test_authenticate_uses_kwargs_username_field_when_username_param_is_none(self, monkeypatch):
        """
        Cubre el branch:
        if username is None: username = kwargs.get(UserModel.USERNAME_FIELD)

        Como USERNAME_FIELD normalmente es "username", no se puede pasar "username" por kwargs
        sin que Python lo bindee al parámetro username. Entonces lo parcheamos a "email".
        """
        user = User.objects.create_user(
            username="kwuser",
            email="kwuser@example.com",
            password="TestPass123!",  # pragma: allowlist secret
        )

        # Parchear USERNAME_FIELD para que el backend lea desde kwargs["email"]
        monkeypatch.setattr(User, "USERNAME_FIELD", "email")

        backend = EmailOrUsernameModelBackend()

        result = backend.authenticate(
            request=None,
            username=None,
            password="TestPass123!",  # pragma: allowlist secret
            email="kwuser@example.com",  # va a kwargs
        )

        assert result == user
