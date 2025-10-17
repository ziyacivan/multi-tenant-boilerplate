from drf_spectacular.utils import extend_schema
from rest_framework import status, views
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from auth.serializers import (
    LoginSerializer,
    RefreshTokenSerializer,
    RegisterSerializer,
    ResendVerificationEmailSerializer,
    VerifyEmailResponseSerializer,
    VerifyEmailSerializer,
)
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


class RefreshTokenView(views.APIView):
    serializer_class = RefreshTokenSerializer
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
        tokens: dict[str, str] = self.service_class.refresh_token(data["refresh"])
        return Response(tokens, status=status.HTTP_200_OK)


class RegisterView(views.APIView):
    throttle_scope = "auth-register"

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    service_class = AuthService()

    @extend_schema(
        responses={
            status.HTTP_200_OK: {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                },
            },
            status.HTTP_400_BAD_REQUEST: {
                "type": "object",
                "properties": {
                    "detail": {"type": "string"},
                },
            },
        },
        request=RegisterSerializer,
    )
    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.service_class.register(**serializer.validated_data)
        return Response(status=status.HTTP_200_OK)


class VerifyEmailView(views.APIView):
    serializer_class = VerifyEmailSerializer
    permission_classes = [AllowAny]
    service_class = AuthService()

    @extend_schema(
        responses={
            status.HTTP_200_OK: {
                "type": "object",
                "properties": {
                    "email": {"type": "string"},
                    "is_verified": {"type": "boolean"},
                },
            },
            status.HTTP_400_BAD_REQUEST: {
                "type": "object",
                "properties": {
                    "detail": {"type": "string"},
                },
            },
        }
    )
    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = self.service_class.verify_email(**serializer.validated_data)
        response_serializer = VerifyEmailResponseSerializer(data)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class ResendVerificationEmailView(views.APIView):
    serializer_class = ResendVerificationEmailSerializer
    permission_classes = [AllowAny]
    service_class = AuthService()

    @extend_schema(
        responses={
            status.HTTP_200_OK: {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                },
            },
            status.HTTP_400_BAD_REQUEST: {
                "type": "object",
                "properties": {
                    "detail": {"type": "string"},
                },
            },
        },
        request=ResendVerificationEmailSerializer,
    )
    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.service_class.resend_verification_email(**serializer.validated_data)
        return Response(status=status.HTTP_200_OK)
