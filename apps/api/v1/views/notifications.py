import hmac

from django.conf import settings
from django.utils import timezone

from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import generics, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.v1.serializers.notifications import DeviceTokenSerializer, NotificationSerializer
from apps.notifications.models import DeviceToken, Notification
from apps.notifications.reminders import send_recurring_reminders


@extend_schema(tags=["notifications"])
class DeviceTokenView(APIView):
    """
    Registra (o actualiza) el token FCM del dispositivo del usuario logueado,
    para poder enviarle notificaciones push. Se llama cada vez que la app
    arranca o cuando Firebase rota el token.

    El token es único a nivel global: si ya estaba asociado a otro usuario
    (instalación anterior desinstalada, token reasignado por Firebase), se
    reasigna al usuario actual en vez de fallar por duplicado.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = DeviceTokenSerializer

    def post(self, request):
        serializer = DeviceTokenSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        token = serializer.validated_data["token"]
        platform = serializer.validated_data["platform"]

        DeviceToken.objects.update_or_create(
            token=token,
            defaults={
                "user": request.user,
                "platform": platform,
                "is_active": True,
            },
        )

        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request):
        """Desactiva el token al cerrar sesión, para no seguir enviándole
        pushes a un dispositivo que ya deslogueó al usuario."""
        token = request.data.get("token")
        if not token:
            return Response(
                {"detail": "Falta el token a desactivar."}, status=status.HTTP_400_BAD_REQUEST
            )

        DeviceToken.objects.filter(token=token, user=request.user).update(is_active=False)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["notifications"])
class NotificationListView(generics.ListAPIView):
    """Historial de avisos del usuario logueado, más recientes primero."""

    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


@extend_schema(tags=["notifications"])
class NotificationUnreadCountView(APIView):
    """Cantidad de avisos sin leer, para el punto de la campanita del dashboard."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses=inline_serializer(
            "NotificationUnreadCount", {"unread": serializers.IntegerField()}
        )
    )
    def get(self, request):
        unread = Notification.objects.filter(user=request.user, read_at__isnull=True).count()
        return Response({"unread": unread})


@extend_schema(tags=["notifications"])
class NotificationMarkReadView(APIView):
    """Marca como leídos todos los avisos del usuario (se llama al abrir la pantalla)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses={204: None})
    def post(self, request):
        Notification.objects.filter(user=request.user, read_at__isnull=True).update(
            read_at=timezone.now()
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(exclude=True)
class RecurringRemindersCronView(APIView):
    """Disparado una vez por día por GitHub Actions: Render free no tiene cron ni shell (D-019 Fase D)."""

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        secret = request.headers.get("X-Cron-Secret", "")
        if not settings.CRON_SECRET or not hmac.compare_digest(secret, settings.CRON_SECRET):
            return Response(status=status.HTTP_403_FORBIDDEN)

        return Response({"sent": send_recurring_reminders()})
