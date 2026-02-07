"""URL configuration for accounts web views (template-based)."""

from django.urls import path

from modules.accounts.interfaces.web_views import (
    WebLoginView,
    WebLogoutView,
    WebPasswordResetView,
    WebRegisterView,
)

app_name = "accounts"

urlpatterns = [
    path("login/", WebLoginView.as_view(), name="login"),
    path("logout/", WebLogoutView.as_view(), name="logout"),
    path("register/", WebRegisterView.as_view(), name="register"),
    path("password-reset/", WebPasswordResetView.as_view(), name="password_reset"),
]
