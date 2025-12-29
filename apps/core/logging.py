"""
Utilidades de logging para la aplicación.
"""

import logging
from functools import wraps

# Logger de seguridad
security_logger = logging.getLogger('security')

# Logger de aplicación
app_logger = logging.getLogger('apps')


def log_login_attempt(username: str, ip_address: str, success: bool):
    """Registra un intento de login."""
    status = "SUCCESS" if success else "FAILED"
    security_logger.info(
        f"LOGIN {status} | User: {username} | IP: {ip_address}"
    )


def log_logout(username: str, ip_address: str):
    """Registra un logout."""
    security_logger.info(
        f"LOGOUT | User: {username} | IP: {ip_address}"
    )


def log_lockout(username: str, ip_address: str):
    """Registra un bloqueo por rate limiting."""
    security_logger.warning(
        f"LOCKOUT | User: {username} | IP: {ip_address} | "
        "Account locked due to multiple failed login attempts"
    )


def log_password_change(username: str, ip_address: str):
    """Registra un cambio de contraseña."""
    security_logger.info(
        f"PASSWORD_CHANGE | User: {username} | IP: {ip_address}"
    )


def log_user_registration(username: str, ip_address: str):
    """Registra un nuevo registro de usuario."""
    security_logger.info(
        f"REGISTRATION | User: {username} | IP: {ip_address}"
    )


def log_permission_denied(username: str, ip_address: str, resource: str):
    """Registra un intento de acceso denegado."""
    security_logger.warning(
        f"PERMISSION_DENIED | User: {username} | IP: {ip_address} | "
        f"Resource: {resource}"
    )


def log_sensitive_action(action: str, username: str, ip_address: str, details: str = ""):
    """Registra una acción sensible."""
    msg = f"{action.upper()} | User: {username} | IP: {ip_address}"
    if details:
        msg += f" | Details: {details}"
    security_logger.info(msg)


def get_client_ip(request) -> str:
    """Obtiene la IP real del cliente, considerando proxies."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', 'unknown')
    return ip


def log_view_access(view_name: str):
    """
    Decorador para loggear acceso a vistas sensibles.
    
    Uso:
        @log_view_access('admin_dashboard')
        def admin_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            username = request.user.username if request.user.is_authenticated else 'anonymous'
            ip = get_client_ip(request)
            app_logger.info(
                f"VIEW_ACCESS | View: {view_name} | User: {username} | IP: {ip}"
            )
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator