import logging
import time

logger = logging.getLogger("apps.performance")


class PermissionsPolicyMiddleware:
    """Agrega el header Permissions-Policy desactivando APIs del navegador no usadas."""

    POLICY = (
        "camera=(), microphone=(), geolocation=(), payment=(), "
        "usb=(), bluetooth=(), interest-cohort=()"
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["Permissions-Policy"] = self.POLICY
        return response


class RequestTimingMiddleware:
    """Loggea duración de requests en milisegundos."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.perf_counter()
        response = self.get_response(request)
        duration_ms = (time.perf_counter() - start) * 1000

        logger.info(
            "REQUEST_TIMING | method=%s path=%s status=%s duration_ms=%.2f",
            request.method,
            request.path,
            response.status_code,
            duration_ms,
        )
        return response
