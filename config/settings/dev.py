from .base import *
from .email_backend import apply_email_settings

# =============================================================================
# DESARROLLO - DEBUG HABILITADO
# =============================================================================
DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# CORS: permite Flutter en desarrollo (emulador Android usa 10.0.2.2)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://10.0.2.2:8000",
]
CORS_ALLOW_ALL_ORIGINS = True  # Solo en desarrollo

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Debug Tollbar
INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
INTERNAL_IPS = ["127.0.0.1"]

# Email to console
apply_email_settings(globals(), default_backend="django.core.mail.backends.console.EmailBackend")

# Destinatario del formulario de feedback de usuarios
FEEDBACK_EMAIL = "kachuknm@gmail.com"

# Resend API key (vacío en dev — se usa console backend)
RESEND_API_KEY = config("RESEND_API_KEY", default="")


# =============================================================================
# LOGGING - Desarrollo
# =============================================================================

# En entornos locales y sandbox evitamos depender de escritura en /logs.
LOGGING["handlers"]["console"]["level"] = "DEBUG"
LOGGING["handlers"]["file"] = {
    "level": "INFO",
    "class": "logging.StreamHandler",
    "formatter": "verbose",
}
LOGGING["handlers"]["error_file"] = {
    "level": "ERROR",
    "class": "logging.StreamHandler",
    "formatter": "verbose",
}
LOGGING["handlers"]["security_file"] = {
    "level": "INFO",
    "class": "logging.StreamHandler",
    "formatter": "security",
}


# ============================================================================
# CSP RELAJADO SOLO PARA DESARROLLO
# ============================================================================

# Mantener default-src sencillo
CSP_DEFAULT_SRC = ("'self'",)

# Permitir estilos desde:
# Estilos: unsafe-inline requerido para estilos dinámicos en templates (ver D-009)
CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",
    "https://cdn.jsdelivr.net",
)

# Permitir scripts desde:
# - tu propio dominio ('self')
# - jsDelivr (Bootstrap bundle, Chart.js)
CSP_SCRIPT_SRC = (
    "'self'",
    "https://cdn.jsdelivr.net",
)

# Fuentes: propias + jsDelivr + data: (para icon fonts, etc.)
CSP_FONT_SRC = (
    "'self'",
    "https://cdn.jsdelivr.net",
    "data:",
)

# Imágenes: propias + data URI
CSP_IMG_SRC = (
    "'self'",
    "data:",
)

# Conexiones: permitir source maps para debugging en desarrollo
CSP_CONNECT_SRC = (
    "'self'",
    "https://cdn.jsdelivr.net",
)
