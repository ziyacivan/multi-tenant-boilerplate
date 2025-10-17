from django.urls import path

from auth.views import (
    LoginView,
    RefreshTokenView,
    RegisterView,
    ResendVerificationEmailView,
    VerifyEmailView,
)

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("register/", RegisterView.as_view(), name="register"),
    path("verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    path(
        "resend-verification-email/",
        ResendVerificationEmailView.as_view(),
        name="resend-verification-email",
    ),
    path("token/refresh/", RefreshTokenView.as_view(), name="token-refresh"),
]
