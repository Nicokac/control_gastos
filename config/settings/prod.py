from .base import *
from decouple import config

DEBUG = False

# Obtener hosts desde variable de entorno
# Formato: "dominio1.com,dominio2.com,www.dominio1.com"
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')

# Eliminar strings vacíos si no hay hosts configurados
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS if host.strip()]

# Validación: No permitir deploy sin ALLOWED_HOSTS configurado
if not ALLOWED_HOSTS:
    raise ValueError(
        "ALLOWED_HOSTS no está configurado. "
        "Define la variable de entorno ALLOWED_HOSTS con los dominios permitidos."
    )

DATABASES = {
    'default':{
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# Security
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Static files with WhiteNoise
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


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
X_FRAME_OPTIONS = 'DENY'

# Previene que el navegador adivine el tipo de contenido
# Protege contra ataques de sniffing de MIME type
SECURE_CONTENT_TYPE_NOSNIFF = True

# Filtro XSS del navegador (legacy, pero no hace daño)
SECURE_BROWSER_XSS_FILTER = True

# Política de Referrer - Controla qué información se envía en el header Referer
# strict-origin-when-cross-origin = Envía origen completo para same-origin,
# solo el origen para cross-origin, nada para downgrade HTTPS->HTTP
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Proxy SSL - Si estás detrás de un proxy/load balancer que maneja SSL
# Descomenta si usas Railway, Render, Heroku, etc.
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

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
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# Edad de la sesión (2 semanas)
SESSION_COOKIE_AGE = 1209600