from django.utils.translation import gettext as _

from drf_spectacular.utils import extend_schema
from rest_framework import status, views
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from auth.serializers import (
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
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
        tokens, related_tenant = self.service_class.validate_credentials(
            data["email"], data["password"]
        )
        return Response(
            tokens,
            status=status.HTTP_200_OK,
            headers={"X-Related-Tenant": related_tenant.pk},
        )


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


class PasswordResetRequestView(views.APIView):
    permission_classes = [AllowAny]
    throttle_classes = []  # TODO: Implement throttling
    service_class = AuthService()

    @extend_schema(
        responses={
            status.HTTP_200_OK: {
                "type": "object",
                "properties": {
                    "detail": {"type": "string"},
                },
            },
        },
        request=PasswordResetRequestSerializer,
    )
    def post(self, request, *args, **kwargs):
        serializer = PasswordResetRequestSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data["email"]
            self.service_class.request_password_reset(email, request)

        return Response(
            {
                "detail": _(
                    "If an account with that email exists, a password reset link has been sent."
                )
            },
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(views.APIView):
    permission_classes = [AllowAny]
    throttle_classes = []  # TODO: Implement throttling
    service_class = AuthService()

    @extend_schema(
        responses={
            status.HTTP_200_OK: {
                "type": "object",
                "properties": {
                    "detail": {"type": "string"},
                },
            },
            status.HTTP_400_BAD_REQUEST: {
                "type": "object",
                "properties": {
                    "detail": {"type": "string"},
                },
            },
        },
        request=PasswordResetConfirmSerializer,
    )
    def post(self, request, *args, **kwargs):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        uidb64 = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password1"]

        success, message = self.service_class.confirm_password_reset(
            uidb64, token, new_password
        )

        if success:
            return Response({"detail": message}, status=status.HTTP_200_OK)
        else:
            return Response({"detail": message}, status=status.HTTP_400_BAD_REQUEST)
