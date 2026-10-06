from django.contrib.auth import get_user_model
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode

from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["email", "username", "password", "password2"]

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError(
                {"password": "Las contraseñas no coinciden."}  # pragma: allowlist secret
            )
        return attrs

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Ya existe una cuenta con este email.")
        return value.lower()

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Este nombre de usuario ya está en uso.")
        return value

    def create(self, validated_data):
        validated_data.pop("password2")
        return User.objects.create_user(**validated_data)


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def get_user(self):
        """Devuelve el usuario activo con ese email, o None si no existe.
        No se expone si el email existe o no — evita enumeración de cuentas."""
        email = self.validated_data["email"]
        return User.objects.filter(email__iexact=email, is_active=True).first()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password2 = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password2"]:
            raise serializers.ValidationError(
                {"new_password": "Las contraseñas no coinciden."}  # pragma: allowlist secret
            )

        try:
            uid = force_bytes(urlsafe_base64_decode(attrs["uid"])).decode()
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError) as err:
            raise serializers.ValidationError({"uid": "Enlace de recuperación inválido."}) from err

        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError(
                {"token": "El enlace de recuperación es inválido o expiró."}
            )

        form = SetPasswordForm(
            user=user,
            data={
                "new_password1": attrs["new_password"],
                "new_password2": attrs["new_password2"],
            },
        )
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)

        attrs["user"] = user
        attrs["form"] = form
        return attrs

    def save(self):
        self.validated_data["form"].save()
        return self.validated_data["user"]


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "default_currency",
            "alert_threshold",
            "financial_month_start_day",
            "email_verified",
        ]
        read_only_fields = ["id", "email", "email_verified"]
