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
    
    # SECRET_KEY - Existencia
    if not settings.SECRET_KEY:
        errors.append("SECRET_KEY no está configurada")
    else:
        # SECRET_KEY - Longitud
        if len(settings.SECRET_KEY) < 50:
            errors.append(f"SECRET_KEY muy corta ({len(settings.SECRET_KEY)} chars, mínimo 50)")
        else:
            # SECRET_KEY - Valores inseguros
            insecure_patterns = [
                'dev-secret', 'secret-key', 'change-me', 'your-secret',
                'django-insecure', 'placeholder', 'xxx', '123456'
            ]
            
            is_insecure = any(
                pattern in settings.SECRET_KEY.lower() 
                for pattern in insecure_patterns
            )
            
            if is_insecure:
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
    hsts_seconds = getattr(settings, 'SECURE_HSTS_SECONDS', 0)
    if not hsts_seconds:
        errors.append("SECURE_HSTS_SECONDS no configurado")
    elif hsts_seconds < 31536000:  # Menos de 1 año
        warnings.append(f"HSTS muy corto ({hsts_seconds}s), recomendado 31536000 (1 año)")
        print(f"⚠️  HSTS configurado: {hsts_seconds} segundos (recomendado: 31536000)")
    else:
        print(f"✅ HSTS configurado: {hsts_seconds} segundos")
    
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
    
    # HSTS Subdomains
    if hsts_seconds and not getattr(settings, 'SECURE_HSTS_INCLUDE_SUBDOMAINS', False):
        warnings.append("SECURE_HSTS_INCLUDE_SUBDOMAINS no está activado")
    
    # Session Cookie HttpOnly
    if not getattr(settings, 'SESSION_COOKIE_HTTPONLY', True):
        warnings.append("SESSION_COOKIE_HTTPONLY debería estar activado")
    
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

    # =========================================================================
    # CHECKS DE RATE LIMITING
    # =========================================================================
    
    # Django-axes instalado
    if 'axes' in settings.INSTALLED_APPS:
        print("✅ Django-axes instalado")
        
        # Verificar configuración
        failure_limit = getattr(settings, 'AXES_FAILURE_LIMIT', None)
        if failure_limit:
            print(f"   • Límite de intentos: {failure_limit}")
        else:
            warnings.append("AXES_FAILURE_LIMIT no configurado")
        
        cooloff = getattr(settings, 'AXES_COOLOFF_TIME', None)
        if cooloff:
            print(f"   • Tiempo de bloqueo: {cooloff} hora(s)")
        else:
            warnings.append("AXES_COOLOFF_TIME no configurado (bloqueo permanente)")
        
        # Verificar middleware
        if 'axes.middleware.AxesMiddleware' in settings.MIDDLEWARE:
            print("   • Middleware configurado")
        else:
            errors.append("AxesMiddleware no está en MIDDLEWARE")
        
        # Verificar backend
        backends = getattr(settings, 'AUTHENTICATION_BACKENDS', [])
        if 'axes.backends.AxesStandaloneBackend' in backends:
            print("   • Backend de autenticación configurado")
        else:
            errors.append("AxesStandaloneBackend no está en AUTHENTICATION_BACKENDS")
    else:
        warnings.append("Django-axes no está instalado (sin rate limiting)")


if __name__ == '__main__':
    check_security()