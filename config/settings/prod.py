# =============================================================================
# VALIDACIONES DE SEGURIDAD
# =============================================================================
from django.core.exceptions import ImproperlyConfigured

from decouple import config

from .base import *

# Validar longitud mínima de SECRET_KEY (50 caracteres recomendado)
if len(SECRET_KEY) < 50:
    raise ImproperlyConfigured(
        "\n"
        "=" * 60 + "\n"
        "❌ ERROR: SECRET_KEY es demasiado corta\n"
        "=" * 60 + "\n"
        f"\n"
        f"Longitud actual: {len(SECRET_KEY)} caracteres\n"
        f"Longitud mínima: 50 caracteres\n"
        "\n"
        "Generar clave segura con:\n"
        '  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"\n'
        "\n"
        "=" * 60
    )

# Validar que no contenga valores inseguros conocidos
INSECURE_KEYS = [
    "dev-secret",
    "secret-key",
    "change-me",
    "your-secret",
    "django-insecure",
    "placeholder",
    "xxx",
    "123",
]

for insecure in INSECURE_KEYS:
    if insecure in SECRET_KEY.lower():
        raise ImproperlyConfigured(
            "\n"
            "=" * 60 + "\n"
            "❌ ERROR: SECRET_KEY contiene valor inseguro\n"
            "=" * 60 + "\n"
            f"\n"
            f"Se detectó '{insecure}' en SECRET_KEY\n"
            "\n"
            "Generar clave segura con:\n"
            '  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"\n'
            "\n"
            "=" * 60
        )

print("✅ SECRET_KEY validada correctamente")


DEBUG = False

# Validación extra: asegurar que DEBUG nunca esté activo en producción
if DEBUG:
    raise ImproperlyConfigured("❌ ERROR: DEBUG=True no está permitido en producción")

# Obtener hosts desde variable de entorno
# Formato: "dominio1.com,dominio2.com,www.dominio1.com"
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="").split(",")

# Eliminar strings vacíos si no hay hosts configurados
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS if host.strip()]

# Validación: No permitir deploy sin ALLOWED_HOSTS configurado
if not ALLOWED_HOSTS:
    raise ValueError(
        "ALLOWED_HOSTS no está configurado. "
        "Define la variable de entorno ALLOWED_HOSTS con los dominios permitidos."
    )
# CSRF Trusted Origins - Necesario para formularios desde dominios externos
# Construir automáticamente desde ALLOWED_HOSTS
CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS if host]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
    }
}

# Security
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Static files with WhiteNoise
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


# =============================================================================
# SEGURIDAD - Headers HTTP
# =============================================================================

# HSTS - Fuerza HTTPS durante 1 año
# Después de activar, el navegador SIEMPRE usará HTTPS para este dominio
SECURE_HSTS_SECONDS = 31536000  # 1 año en segundos
SECURE_HSTS_INCLUDE_SUBDOMAINS = True  # Aplica a subdominios
SECURE_HSTS_PRELOAD = True  # Permite inclusión en lista preload de navegadores

# SSL Redirect - Redirige HTTP a HTTPS automáticamente
SECURE_SSL_REDIRECT = True

# Protección contra Clickjacking
# DENY = No permite que la página sea embebida en iframe de ningún sitio
# SAMEORIGIN = Solo permite iframe del mismo dominio
X_FRAME_OPTIONS = "DENY"

# Previene que el navegador adivine el tipo de contenido
# Protege contra ataques de sniffing de MIME type
SECURE_CONTENT_TYPE_NOSNIFF = True

# Filtro XSS del navegador (legacy, pero no hace daño)
SECURE_BROWSER_XSS_FILTER = True

# Política de Referrer - Controla qué información se envía en el header Referer
# strict-origin-when-cross-origin = Envía origen completo para same-origin,
# solo el origen para cross-origin, nada para downgrade HTTPS->HTTP
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# Proxy SSL - Si estás detrás de un proxy/load balancer que maneja SSL
# Descomenta si usas Railway, Render, Heroku, etc.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# =============================================================================
# SEGURIDAD - Cookies
# =============================================================================

# Cookies solo se envían por HTTPS
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Cookies HttpOnly - No accesibles desde JavaScript
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# SameSite - Protección contra CSRF
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# Edad de la sesión (2 semanas)
SESSION_COOKIE_AGE = 1209600


# =============================================================================
# CONTENT SECURITY POLICY (CSP)
# =============================================================================

# Política de seguridad de contenido
# Controla qué recursos puede cargar la página

# Fuentes por defecto: solo mismo origen
CSP_DEFAULT_SRC = ("'self'",)

# Scripts: mismo origen + CDNs necesarios
# TODO: Eliminar 'unsafe-inline' migrando scripts inline a archivos estáticos
# Esto es una deuda técnica de seguridad - ver issue #XX
CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-inline'",  # DEUDA TÉCNICA: Necesario para scripts inline de Bootstrap/Chart.js
    "https://cdn.jsdelivr.net",  # Bootstrap, Chart.js, etc.
    "https://cdnjs.cloudflare.com",
)

# Estilos: mismo origen + CDNs
# TODO: Eliminar 'unsafe-inline' usando nonces o migrando estilos inline
CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",  # DEUDA TÉCNICA: Necesario para estilos inline de Bootstrap
    "https://cdn.jsdelivr.net",
    "https://fonts.googleapis.com",
)

# Fuentes
CSP_FONT_SRC = (
    "'self'",
    "https://cdn.jsdelivr.net",
    "https://fonts.gstatic.com",
)

# Imágenes
CSP_IMG_SRC = (
    "'self'",
    "data:",  # Para imágenes base64
    "https:",  # Permitir imágenes HTTPS externas
)

# Conexiones (fetch, XHR, WebSocket)
CSP_CONNECT_SRC = ("'self'",)

# Frames: ninguno (ya tenemos X-Frame-Options)
CSP_FRAME_SRC = ("'none'",)

# Objetos (Flash, etc.): ninguno
CSP_OBJECT_SRC = ("'none'",)

# Base URI
CSP_BASE_URI = ("'self'",)

# Form actions
CSP_FORM_ACTION = ("'self'",)


# =============================================================================
# DJANGO-AXES - Configuración de Producción
# =============================================================================

# Más estricto en producción
AXES_FAILURE_LIMIT = 5  # Mantener en 5
AXES_COOLOFF_TIME = 2  # 2 horas en producción

# Para proxies/load balancers (Railway, Render, Heroku, etc.)
# Usar AXES_IPWARE_PROXY_COUNT y AXES_IPWARE_META_PRECEDENCE_ORDER (v6+)
AXES_IPWARE_PROXY_COUNT = 1
AXES_IPWARE_META_PRECEDENCE_ORDER = (
    "HTTP_X_FORWARDED_FOR",
    "HTTP_X_REAL_IP",
    "REMOTE_ADDR",
)

# Logging de intentos
AXES_VERBOSE = True

# No bloquear requests GET (solo POST de login)
AXES_ONLY_ADMIN_SITE = False
AXES_NEVER_LOCKOUT_GET = True


# =============================================================================
# LOGGING - Producción
# =============================================================================

# Sobrescribir configuración de logging para producción
LOGGING["handlers"]["console"]["level"] = "WARNING"  # Menos verbose en consola

# Agregar handler para logs críticos (opcional: enviar por email)
LOGGING["handlers"]["mail_admins"] = {
    "level": "ERROR",
    "class": "django.utils.log.AdminEmailHandler",
    "include_html": True,
}

# Agregar mail_admins a errores de request
LOGGING["loggers"]["django.request"]["handlers"].append("mail_admins")

# Configurar ADMINS para recibir emails de errores
# ADMINS = [('Tu Nombre', 'tu@email.com')]
