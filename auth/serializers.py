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
