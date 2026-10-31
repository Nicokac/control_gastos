"""
Tests para el modelo DeviceToken.
"""

from django.db import IntegrityError

import pytest

from apps.notifications.models import DevicePlatform, DeviceToken


@pytest.mark.django_db
class TestDeviceTokenModel:
    def test_crear_token(self, user):
        device = DeviceToken.objects.create(user=user, token="fcm-abc123")

        assert device.pk is not None
        assert device.user == user
        assert device.token == "fcm-abc123"

    def test_platform_por_defecto_es_android(self, user):
        device = DeviceToken.objects.create(user=user, token="fcm-abc123")

        assert device.platform == DevicePlatform.ANDROID

    def test_is_active_por_defecto_true(self, user):
        device = DeviceToken.objects.create(user=user, token="fcm-abc123")

        assert device.is_active is True

    def test_token_es_unico(self, user, other_user):
        DeviceToken.objects.create(user=user, token="fcm-duplicado")

        with pytest.raises(IntegrityError):
            DeviceToken.objects.create(user=other_user, token="fcm-duplicado")

    def test_str_representation(self, user):
        device = DeviceToken.objects.create(user=user, token="fcm-abc123456789")

        result = str(device)

        assert str(user) in result

    def test_un_usuario_puede_tener_varios_dispositivos(self, user):
        DeviceToken.objects.create(user=user, token="fcm-celular")
        DeviceToken.objects.create(user=user, token="fcm-tablet")

        assert DeviceToken.objects.filter(user=user).count() == 2
