from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class RefreshTokenSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class RegisterResponseSerializer(serializers.Serializer):
    email = serializers.EmailField()
    verification_code = serializers.CharField()
    verification_code_expires_at = serializers.DateTimeField()


class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    verification_code = serializers.CharField()


class VerifyEmailResponseSerializer(serializers.Serializer):
    email = serializers.EmailField()
    is_verified = serializers.BooleanField()


class ResendVerificationEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password1 = serializers.CharField(
        required=True, write_only=True, style={"input_type": "password"}
    )
    new_password2 = serializers.CharField(
        required=True, write_only=True, style={"input_type": "password"}
    )

    def validate(self, data):
        if data["new_password1"] != data["new_password2"]:
            raise serializers.ValidationError(_("Passwords do not match."))

        try:
            validate_password(data["new_password1"])
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))

        return data
