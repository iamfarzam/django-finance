"""URL configuration for accounts module."""

from django.urls import path

from modules.accounts.interfaces.views import (
    ChangePasswordView,
    LoginView,
    LogoutView,
    ProfileView,
    RefreshTokenView,
    RegisterView,
    RequestPasswordResetView,
    ResendVerificationView,
    ResetPasswordView,
    UpdateProfileView,
    VerifyEmailView,
)

app_name = "accounts"

urlpatterns = [
    # Registration
    path("register/", RegisterView.as_view(), name="register"),
    # Authentication
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", RefreshTokenView.as_view(), name="token-refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    # Email verification
    path("verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    path("resend-verification/", ResendVerificationView.as_view(), name="resend-verification"),
    # Password management
    path("password/reset/request/", RequestPasswordResetView.as_view(), name="password-reset-request"),
    path("password/reset/", ResetPasswordView.as_view(), name="password-reset"),
    path("password/change/", ChangePasswordView.as_view(), name="password-change"),
    # Profile
    path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/update/", UpdateProfileView.as_view(), name="profile-update"),
]
