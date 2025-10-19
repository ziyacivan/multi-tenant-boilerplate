from django.urls import path

from auth.views import (
    LoginView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RefreshTokenView,
    RegisterView,
    ResendVerificationEmailView,
    VerifyEmailView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", RefreshTokenView.as_view(), name="token-refresh"),
    path("email/verify/", VerifyEmailView.as_view(), name="verify-email"),
    path(
        "email/resend-verification/",
        ResendVerificationEmailView.as_view(),
        name="resend-verification-email",
    ),
    path(
        "password/reset/",
        PasswordResetRequestView.as_view(),
        name="password-reset-request",
    ),
    path(
        "password/reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
]
