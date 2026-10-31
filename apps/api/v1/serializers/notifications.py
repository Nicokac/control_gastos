from rest_framework import serializers

from apps.notifications.models import DevicePlatform


class DeviceTokenSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=255)
    platform = serializers.ChoiceField(
        choices=DevicePlatform.choices, default=DevicePlatform.ANDROID
    )
