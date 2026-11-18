from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

# Temporal (DT-119): ver qué cadena de IPs llega detrás de Cloudflare/Render para
# elegir un header que el cliente no pueda falsificar. Se borra con el fix.
_IP_KEYS = (
    "REMOTE_ADDR",
    "HTTP_X_FORWARDED_FOR",
    "HTTP_X_REAL_IP",
    "HTTP_CF_CONNECTING_IP",
    "HTTP_TRUE_CLIENT_IP",
    "HTTP_X_FORWARDED_HOST",
    "HTTP_HOST",
)


class ClientIpDebugView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAdminUser]

    def get(self, request):
        return Response({key: request.META.get(key) for key in _IP_KEYS})
