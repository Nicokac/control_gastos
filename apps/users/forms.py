"""Formulario de autenticación y perfil de usuario."""

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db.models import Q

from .models import User


class LoginForm(AuthenticationForm):
    """Formulario de login personalizado con mensajes específicos."""

    username = forms.CharField(
        label="Email o Usuario",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Email o nombre de usuario",
                "autofocus": True,
            }
        ),
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Contraseña"}),
    )

    error_messages = {
        "invalid_login": "Usuario o contraseña incorrectos. Verificá tus datos.",
        "inactive": "Esta cuenta está desactiva.",
    }

    def clean_username(self):
        """
        Normaliza el identificador de login.
        - strip()
        - si parece email, lo pasa a lower()
        """
        username = self.cleaned_data.get("username")
        if isinstance(username, str):
            username = username.strip()
            if "@" in username:
                username = username.lower()
        return username

    def _user_exists(self, identifier: str) -> bool:
        return User.objects.filter(Q(username=identifier) | Q(email=identifier)).exists()

    def _authenticate(self, identifier: str, password: str):
        return authenticate(self.request, username=identifier, password=password)

    def clean(self):
        """Validación con mensajes específicos (Ley de Postel)."""
        cleaned = super().clean()

        username = cleaned.get("username")
        password = cleaned.get("password")

        if not username or not password:
            return cleaned

        # Buscar usuario por username o email
        user = (
            User.objects.filter(Q(username=username) | Q(email=username))
            .only("id", "is_active", "password", "username", "email")
            .first()
        )

        if user is None:
            raise forms.ValidationError(
                "No existe una cuenta con ese usuario o email.", code="user_not_found"
            )

        if not user.is_active:
            raise forms.ValidationError(self.error_messages["inactive"], code="inactive")

        # Password incorrecta (sin depender de authenticate, evita caer al genérico)
        if not user.check_password(password):
            raise forms.ValidationError(
                "Contraseña incorrecta. Intentá nuevamente.", code="invalid_password"
            )

        # OK: credenciales válidas -> dejamos que el LoginView autentique realmente.
        return cleaned


class RegisterForm(UserCreationForm):
    """Formulario de registro de nuevos usuarios."""

    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "tu@email.com"}),
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
        widgets = {
            "username": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Nombre de usuario"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Contraseña"}
        )
        self.fields["password2"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Confirmar contraseña"}
        )

        # Mensaje de ayuda más claros
        self.fields["password1"].help_text = "Mínimo 8 caracteres."
        self.fields["password2"].help_text = ""

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if isinstance(email, str):
            email = email.strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con este email.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if isinstance(username, str):
            username = username.strip()

        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso.")
        return username


class ProfileForm(forms.ModelForm):
    """Formulario para editar perfil de usuario."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "default_currency", "alert_threshold"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre"}),
            "last_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Apellido"}
            ),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email"}),
            "default_currency": forms.Select(attrs={"class": "form-select"}),
            "alert_threshold": forms.NumberInput(
                attrs={"class": "form-control", "min": 1, "max": 100}
            ),
        }
        labels = {
            "first_name": "Nombre",
            "last_name": "Apellido",
            "email": "Email",
            "default_currency": "Moneda principal",
            "alert_threshold": "Umbral de alerta (%)",
        }
        help_texts = {
            "alert_threshold": "Te avisaremos cuando alcances este porcentaje del presupuesto.",
        }

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if isinstance(email, str):
            email = email.strip().lower()

        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Este mail ya está en uso por otra cuenta.")
        return email

    def clean_alert_threshold(self):
        value = self.cleaned_data.get("alert_threshold")
        if value is None:
            return value
        if not (1 <= value <= 100):
            raise forms.ValidationError("El umbral debe estar entre 1 y 100.")
        return value
