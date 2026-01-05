"""
Configuración centralizada de email.

- Dev: usa console backend por defecto.
- Prod: si hay variables SMTP, usa SMTP; si no, queda silenciado.
"""

from decouple import config


def apply_email_settings(globals_dict, *, default_backend: str | None = None) -> None:
    """
    Inyecta settings EMAIL_* en el módulo que lo llama (dev/prod),
    sin importar dónde se defina.

    Uso:
        from .email_backend import apply_email_settings
        apply_email_settings(globals(), default_backend="django.core.mail.backends.console.EmailBackend")
    """
    env_backend = config("EMAIL_BACKEND", default="")
    if env_backend:
        globals_dict["EMAIL_BACKEND"] = env_backend

    # Backend por defecto (si el caller lo define)
    if default_backend:
        globals_dict.setdefault("EMAIL_BACKEND", default_backend)

    # Destinatario ADMINS (lo mantenés en prod.py; acá solo ayudamos con from/server)
    admin_email = globals_dict.get("ADMIN_EMAIL") or config("ADMIN_EMAIL", default="")

    globals_dict.setdefault(
        "DEFAULT_FROM_EMAIL",
        config("DEFAULT_FROM_EMAIL", default=admin_email or "noreply@localhost"),
    )
    globals_dict.setdefault(
        "SERVER_EMAIL", config("SERVER_EMAIL", default=globals_dict["DEFAULT_FROM_EMAIL"])
    )

    # Si hay SMTP, lo habilitamos (esto permite que mail_admins funcione)
    email_host = config("EMAIL_HOST", default="")
    if not email_host:
        return  # No hay SMTP configurado → no tocamos más nada

    globals_dict["EMAIL_BACKEND"] = "django.core.mail.backends.smtp.EmailBackend"
    globals_dict["EMAIL_HOST"] = email_host
    globals_dict["EMAIL_PORT"] = config("EMAIL_PORT", default=587, cast=int)
    globals_dict["EMAIL_HOST_USER"] = config("EMAIL_HOST_USER", default="")
    globals_dict["EMAIL_HOST_PASSWORD"] = config("EMAIL_HOST_PASSWORD", default="")
    globals_dict["EMAIL_USE_TLS"] = config("EMAIL_USE_TLS", default=True, cast=bool)
    globals_dict["EMAIL_USE_SSL"] = config("EMAIL_USE_SSL", default=False, cast=bool)

    # Timeout para evitar cuelgues por SMTP
    globals_dict["EMAIL_TIMEOUT"] = config("EMAIL_TIMEOUT", default=10, cast=int)
