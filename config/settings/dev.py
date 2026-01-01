from .base import *

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

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
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


# ============================================================================
# CSP RELAJADO SOLO PARA DESARROLLO
# ============================================================================

# Mantener default-src sencillo
CSP_DEFAULT_SRC = ("'self'",)

# Permitir estilos desde:
# - tu propio dominio ('self')
# - estilos inline (por ahora, para no pelear con nada en dev)
# - CDN de jsDelivr (Bootstrap, Bootstrap Icons)
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
