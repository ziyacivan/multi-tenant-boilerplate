from drf_spectacular.utils import extend_schema
from rest_framework import status, views
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from auth.serializers import LoginSerializer
from auth.services import AuthService


class LoginView(views.APIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    service_class = AuthService()

    @extend_schema(
        responses={
            status.HTTP_200_OK: {
                "type": "object",
                "properties": {
                    "refresh": {
                        "type": "string",
                    },
                    "access": {
                        "type": "string",
                    },
                },
            },
            status.HTTP_400_BAD_REQUEST: {
                "type": "object",
                "properties": {
                    "detail": {
                        "type": "string",
                    },
                },
            },
        }
    )
    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        tokens: dict[str, str] = self.service_class.validate_credentials(
            data["email"], data["password"]
        )
        return Response(tokens, status=status.HTTP_200_OK)
