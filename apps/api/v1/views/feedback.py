from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.v1.serializers.feedback import FeedbackSerializer
from apps.core.utils import send_feedback_email

TIPO_LABELS = {
    "bug": "Bug / Falla",
    "mejora": "Sugerencia de mejora",
    "pregunta": "Pregunta",
    "otro": "Otro",
}


@extend_schema(tags=["feedback"])
class FeedbackView(APIView):
    """Recibe feedback desde mobile y lo envía por email al administrador,
    igual que el formulario web (ver apps.core.views.FeedbackView). Si el
    cliente adjunta technical_context (último error de red capturado), se
    incluye en el cuerpo del email para evitar que el usuario tenga que
    describir el error técnico a mano (DT-084)."""

    permission_classes = [IsAuthenticated]
    serializer_class = FeedbackSerializer

    def post(self, request):
        serializer = FeedbackSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        tipo = serializer.validated_data["tipo"]
        mensaje = serializer.validated_data["mensaje"]
        technical_context = serializer.validated_data.get("technical_context", "")
        tipo_label = TIPO_LABELS.get(tipo, tipo)

        subject = f"[Control de Gastos - Mobile] {tipo_label} — {user.username}"
        body = f"Usuario: {user.username}\nEmail: {user.email}\nTipo: {tipo_label}\n---\n{mensaje}"
        if technical_context:
            body += f"\n---\nContexto técnico (último error de red capturado):\n{technical_context}"

        sent = send_feedback_email(subject, body, log_context=f"mobile, usuario {user.username}")

        if sent:
            return Response(
                {"detail": "Gracias, tu reporte fue enviado correctamente."},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"detail": "No se pudo enviar el reporte. Intentá de nuevo más tarde."},
            status=status.HTTP_502_BAD_GATEWAY,
        )
