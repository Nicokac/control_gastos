#!/usr/bin/env python
"""
Script para verificar configuración de seguridad antes del deploy.
Ejecutar: python scripts/check_security.py
"""

import os
import sys
from pathlib import Path

import django
from django.conf import settings


def setup_django() -> None:
    """Inicializa entorno Django."""
    root_dir = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root_dir))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")
    django.setup()


def check_security() -> int:
    """Verifica configuraciones de seguridad."""
    errors: list[str] = []
    warnings: list[str] = []

    print("=" * 60)
    print("🔒 VERIFICACIÓN DE SEGURIDAD - Control de Gastos")
    print("=" * 60)
    print()

    # =========================================================================
    # CHECKS CRÍTICOS (Bloquean deploy)
    # =========================================================================

    # SECRET_KEY
    if not settings.SECRET_KEY:
        errors.append("SECRET_KEY no está configurada")
    elif len(settings.SECRET_KEY) < 50:
        errors.append(f"SECRET_KEY muy corta ({len(settings.SECRET_KEY)} chars, mínimo 50)")
    else:
        insecure_patterns = [
            "dev-secret",
            "secret-key",
            "change-me",
            "your-secret",
            "django-insecure",
            "placeholder",
            "xxx",
            "123456",
        ]
        if any(p in settings.SECRET_KEY.lower() for p in insecure_patterns):
            errors.append("SECRET_KEY contiene patrones inseguros")
        else:
            print(f"✅ SECRET_KEY configurada ({len(settings.SECRET_KEY)} chars)")

    # DEBUG
    if settings.DEBUG:
        errors.append("DEBUG está activado en producción")
    else:
        print("✅ DEBUG desactivado")

    # ALLOWED_HOSTS
    if not settings.ALLOWED_HOSTS:
        errors.append("ALLOWED_HOSTS está vacío")
    else:
        print(f"✅ ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")

    # HSTS
    hsts_seconds = getattr(settings, "SECURE_HSTS_SECONDS", 0)
    if not hsts_seconds:
        errors.append("SECURE_HSTS_SECONDS no configurado")
    elif hsts_seconds < 31_536_000:
        warnings.append(f"HSTS muy corto ({hsts_seconds}s)")
    else:
        print(f"✅ HSTS configurado: {hsts_seconds} segundos")

    # SSL Redirect
    if not getattr(settings, "SECURE_SSL_REDIRECT", False):
        errors.append("SECURE_SSL_REDIRECT no está activado")
    else:
        print("✅ SSL Redirect activado")

    # =========================================================================
    # CHECKS IMPORTANTES (Warnings)
    # =========================================================================

    if getattr(settings, "X_FRAME_OPTIONS", None) not in {"DENY", "SAMEORIGIN"}:
        warnings.append("X_FRAME_OPTIONS debería ser DENY o SAMEORIGIN")

    if not getattr(settings, "SESSION_COOKIE_SECURE", False):
        warnings.append("SESSION_COOKIE_SECURE no está activado")

    if not getattr(settings, "CSRF_COOKIE_SECURE", False):
        warnings.append("CSRF_COOKIE_SECURE no está activado")

    if not getattr(settings, "SECURE_CONTENT_TYPE_NOSNIFF", False):
        warnings.append("SECURE_CONTENT_TYPE_NOSNIFF no está activado")

    if not getattr(settings, "SECURE_REFERRER_POLICY", None):
        warnings.append("SECURE_REFERRER_POLICY no configurado")

    # =========================================================================
    # CHECKS RATE LIMITING (axes)
    # =========================================================================

    if "axes" not in settings.INSTALLED_APPS:
        warnings.append("Django-axes no está instalado (sin rate limiting)")

    # =========================================================================
    # CHECKS LOGGING
    # =========================================================================

    if not getattr(settings, "LOGGING", None):
        warnings.append("LOGGING no está configurado")

    # =========================================================================
    # RESUMEN
    # =========================================================================

    print()
    print("=" * 60)

    if errors:
        print("❌ ERRORES CRÍTICOS:")
        for e in errors:
            print(f"   • {e}")

    if warnings:
        print("\n⚠️  ADVERTENCIAS:")
        for w in warnings:
            print(f"   • {w}")

    if errors:
        print("\n🚫 Deploy BLOQUEADO")
        return 1

    print("\n🚀 Deploy PERMITIDO")
    return 0


def main() -> None:
    setup_django()
    sys.exit(check_security())


if __name__ == "__main__":
    main()
