from rest_framework import serializers

from apps.notifications.models import DevicePlatform, Notification


class DeviceTokenSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=255)
    platform = serializers.ChoiceField(
        choices=DevicePlatform.choices, default=DevicePlatform.ANDROID
    )


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "type", "title", "body", "created_at", "read_at"]
