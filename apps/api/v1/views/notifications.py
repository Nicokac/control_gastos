from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.v1.serializers.notifications import DeviceTokenSerializer
from apps.notifications.models import DeviceToken


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
