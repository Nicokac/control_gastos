import logging

from django.conf import settings

import firebase_admin
from firebase_admin import credentials, messaging

from apps.notifications.models import DeviceToken

logger = logging.getLogger("apps.notifications")

# Errores con los que Firebase indica que el token ya no sirve (app desinstalada,
# token rotado o de otro proyecto). Cualquier otro error es transitorio y no
# justifica desactivar el dispositivo.
INVALID_TOKEN_ERRORS = (messaging.UnregisteredError, messaging.SenderIdMismatchError)


def _get_firebase_app():
    try:
        return firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        return firebase_admin.initialize_app(cred)


def send_push_to_user(
    user, title: str, body: str, data: dict | None = None, channel_id: str | None = None
) -> int:
    """Envía un push a todos los dispositivos activos del usuario y devuelve cuántos lo recibieron."""
    if not settings.FIREBASE_CREDENTIALS_PATH:
        logger.warning("PUSH_DISABLED | FIREBASE_CREDENTIALS_PATH vacío | user_id=%s", user.pk)
        return 0

    tokens = list(
        DeviceToken.objects.filter(user=user, is_active=True).values_list("token", flat=True)
    )
    if not tokens:
        return 0

    # El campo `token` guarda el Firebase Installation ID (FID) que registra la app;
    # `tokens=` (tokens de registro FCM) está deprecado en firebase-admin 7.
    message = messaging.MulticastMessage(
        fids=tokens,
        notification=messaging.Notification(title=title, body=body),
        data=data or {},
        # Sin canal explícito, Android usa el canal por defecto del manifest (recordatorios).
        android=(
            messaging.AndroidConfig(
                notification=messaging.AndroidNotification(channel_id=channel_id)
            )
            if channel_id
            else None
        ),
    )
    response = messaging.send_each_for_multicast(message, app=_get_firebase_app())

    invalid_tokens = [
        token
        for token, result in zip(tokens, response.responses)
        if not result.success and isinstance(result.exception, INVALID_TOKEN_ERRORS)
    ]
    if invalid_tokens:
        DeviceToken.objects.filter(token__in=invalid_tokens).update(is_active=False)

    logger.info(
        "PUSH_SENT | user_id=%s success=%s failure=%s deactivated=%s",
        user.pk,
        response.success_count,
        response.failure_count,
        len(invalid_tokens),
    )
    return response.success_count
