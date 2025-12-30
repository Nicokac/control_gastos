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

    def clean(self):
        """Validación con mensajes específicos (Ley de Postel)."""
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username and password:
            # Verificar si el usuario existe
            user_exists = User.objects.filter(Q(username=username) | Q(email=username)).exists()

            if not user_exists:
                raise forms.ValidationError(
                    "No existe una cuenta con ese usuario o email.", code="user_not_found"
                )

            # Intentar autenticar
            self.user_cache = authenticate(self.request, username=username, password=password)

            if self.user_cache is None:
                raise forms.ValidationError(
                    "Contraseña incorrecta. Intentá nuevamente.", code="invalid_password"
                )

            if not self.user_cache.is_active:
                raise forms.ValidationError(self.error_messages["inactive"], code="inactive")

        return self.cleaned_data


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
        """Valida que el email no esté en uso."""
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con este email.")
        return email

    def clean_username(self):
        """Valida que el username no esté en uso."""
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username).exists():
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
        """Valida que el email no esté en uso por otro usuario."""
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Este mail ya está en uso por otra cuenta.")
        return email
