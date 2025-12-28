#!/usr/bin/env python
"""
Script para verificar configuración de seguridad antes del deploy.
Ejecutar: python scripts/check_security.py
"""

import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')

import django
django.setup()

from django.conf import settings


def check_security():
    """Verifica configuraciones de seguridad."""
    errors = []
    warnings = []
    
    print("=" * 60)
    print("🔒 VERIFICACIÓN DE SEGURIDAD - Control de Gastos")
    print("=" * 60)
    print()
    
    # =========================================================================
    # CHECKS CRÍTICOS (Bloquean deploy)
    # =========================================================================
    
    # SECRET_KEY
    if 'dev-secret' in settings.SECRET_KEY.lower() or len(settings.SECRET_KEY) < 50:
        errors.append("SECRET_KEY insegura o muy corta")
    else:
        print("✅ SECRET_KEY configurada correctamente")
    
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
    if not getattr(settings, 'SECURE_HSTS_SECONDS', 0):
        errors.append("SECURE_HSTS_SECONDS no configurado")
    else:
        print(f"✅ HSTS configurado: {settings.SECURE_HSTS_SECONDS} segundos")
    
    # SSL Redirect
    if not getattr(settings, 'SECURE_SSL_REDIRECT', False):
        errors.append("SECURE_SSL_REDIRECT no está activado")
    else:
        print("✅ SSL Redirect activado")
    
    # =========================================================================
    # CHECKS IMPORTANTES (Warnings)
    # =========================================================================
    
    # X-Frame-Options
    x_frame = getattr(settings, 'X_FRAME_OPTIONS', None)
    if x_frame not in ['DENY', 'SAMEORIGIN']:
        warnings.append(f"X_FRAME_OPTIONS debería ser 'DENY' o 'SAMEORIGIN', actual: {x_frame}")
    else:
        print(f"✅ X_FRAME_OPTIONS: {x_frame}")
    
    # Session Cookie Secure
    if not getattr(settings, 'SESSION_COOKIE_SECURE', False):
        warnings.append("SESSION_COOKIE_SECURE no está activado")
    else:
        print("✅ SESSION_COOKIE_SECURE activado")
    
    # CSRF Cookie Secure
    if not getattr(settings, 'CSRF_COOKIE_SECURE', False):
        warnings.append("CSRF_COOKIE_SECURE no está activado")
    else:
        print("✅ CSRF_COOKIE_SECURE activado")
    
    # Content Type Nosniff
    if not getattr(settings, 'SECURE_CONTENT_TYPE_NOSNIFF', False):
        warnings.append("SECURE_CONTENT_TYPE_NOSNIFF no está activado")
    else:
        print("✅ SECURE_CONTENT_TYPE_NOSNIFF activado")
    
    # Referrer Policy
    referrer = getattr(settings, 'SECURE_REFERRER_POLICY', None)
    if not referrer:
        warnings.append("SECURE_REFERRER_POLICY no configurado")
    else:
        print(f"✅ SECURE_REFERRER_POLICY: {referrer}")
    
    # =========================================================================
    # RESUMEN
    # =========================================================================
    
    print()
    print("=" * 60)
    
    if errors:
        print("❌ ERRORES CRÍTICOS (bloquean deploy):")
        for error in errors:
            print(f"   • {error}")
        print()
    
    if warnings:
        print("⚠️  ADVERTENCIAS (recomendado corregir):")
        for warning in warnings:
            print(f"   • {warning}")
        print()
    
    if not errors and not warnings:
        print("✅ ¡Todas las verificaciones pasaron!")
    
    print("=" * 60)
    
    # Exit code
    if errors:
        print("\n🚫 Deploy BLOQUEADO - Corrige los errores críticos")
        sys.exit(1)
    elif warnings:
        print("\n⚠️  Deploy PERMITIDO con advertencias")
        sys.exit(0)
    else:
        print("\n🚀 Deploy LISTO")
        sys.exit(0)


if __name__ == '__main__':
    check_security()