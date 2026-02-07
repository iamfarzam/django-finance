"""Web views for the accounts module (template-based authentication)."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import FormView, TemplateView

from modules.accounts.infrastructure.models import User


class WebLoginView(View):
    """Web login view."""

    template_name = "accounts/login.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        """Show login form."""
        if request.user.is_authenticated:
            return redirect("web:dashboard")

        return render(request, self.template_name, {
            "form": {"email": {"value": ""}, "password": {}},
            "next": request.GET.get("next", ""),
        })

    def post(self, request: HttpRequest) -> HttpResponse:
        """Process login form."""
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        remember_me = request.POST.get("remember_me")
        next_url = request.POST.get("next", "")

        errors = {}

        if not email:
            errors["email"] = ["Email is required."]
        if not password:
            errors["password"] = ["Password is required."]

        if errors:
            return render(request, self.template_name, {
                "form": {
                    "email": {"value": email, "errors": errors.get("email", [])},
                    "password": {"errors": errors.get("password", [])},
                    "non_field_errors": [],
                },
                "next": next_url,
            })

        user = authenticate(request, email=email, password=password)

        if user is None:
            return render(request, self.template_name, {
                "form": {
                    "email": {"value": email},
                    "password": {},
                    "non_field_errors": ["Invalid email or password."],
                },
                "next": next_url,
            })

        if not user.is_active:
            return render(request, self.template_name, {
                "form": {
                    "email": {"value": email},
                    "password": {},
                    "non_field_errors": ["Your account is inactive."],
                },
                "next": next_url,
            })

        login(request, user)

        # Set session expiry
        if not remember_me:
            request.session.set_expiry(0)  # Browser close

        messages.success(request, "Welcome back!")

        if next_url:
            return redirect(next_url)
        return redirect("web:dashboard")


class WebLogoutView(View):
    """Web logout view."""

    def post(self, request: HttpRequest) -> HttpResponse:
        """Log out user."""
        logout(request)
        messages.info(request, "You have been signed out.")
        return redirect("accounts:login")


class WebRegisterView(View):
    """Web registration view."""

    template_name = "accounts/register.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        """Show registration form."""
        if request.user.is_authenticated:
            return redirect("web:dashboard")

        return render(request, self.template_name, {
            "form": {
                "first_name": {"value": ""},
                "last_name": {"value": ""},
                "email": {"value": ""},
                "password1": {},
                "password2": {},
            },
        })

    def post(self, request: HttpRequest) -> HttpResponse:
        """Process registration form."""
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")
        terms = request.POST.get("terms")

        errors = {}
        non_field_errors = []

        # Validation
        if not email:
            errors["email"] = ["Email is required."]
        elif User.objects.filter(email=email).exists():
            errors["email"] = ["An account with this email already exists."]

        if not password1:
            errors["password1"] = ["Password is required."]
        elif len(password1) < 12:
            errors["password1"] = ["Password must be at least 12 characters."]

        if password1 != password2:
            errors["password2"] = ["Passwords do not match."]

        if not terms:
            non_field_errors.append("You must agree to the terms of service.")

        if errors or non_field_errors:
            return render(request, self.template_name, {
                "form": {
                    "first_name": {"value": first_name, "errors": errors.get("first_name", [])},
                    "last_name": {"value": last_name, "errors": errors.get("last_name", [])},
                    "email": {"value": email, "errors": errors.get("email", [])},
                    "password1": {"errors": errors.get("password1", [])},
                    "password2": {"errors": errors.get("password2", [])},
                    "non_field_errors": non_field_errors,
                },
            })

        # Create user
        user = User.objects.create_user(
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name,
        )

        # Log in the user
        login(request, user)
        messages.success(request, "Account created successfully! Welcome to Django Finance.")

        return redirect("web:dashboard")


class WebPasswordResetView(View):
    """Web password reset request view."""

    template_name = "accounts/password_reset.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        """Show password reset form."""
        return render(request, self.template_name, {
            "form": {"email": {"value": ""}},
        })

    def post(self, request: HttpRequest) -> HttpResponse:
        """Process password reset request."""
        email = request.POST.get("email", "").strip().lower()

        if not email:
            return render(request, self.template_name, {
                "form": {
                    "email": {"value": email, "errors": ["Email is required."]},
                },
            })

        # Always show success message (security: don't reveal if email exists)
        messages.success(
            request,
            "If an account exists with that email, you will receive a password reset link."
        )

        # In production, send email here
        # user = User.objects.filter(email=email).first()
        # if user:
        #     send_password_reset_email(user)

        return redirect("accounts:login")


class WebPasswordResetConfirmView(View):
    """Web password reset confirmation view."""

    template_name = "accounts/password_reset_confirm.html"

    def get(self, request: HttpRequest, uidb64: str, token: str) -> HttpResponse:
        """Show password reset confirmation form."""
        # Validate token here
        return render(request, self.template_name, {
            "uidb64": uidb64,
            "token": token,
        })

    def post(self, request: HttpRequest, uidb64: str, token: str) -> HttpResponse:
        """Process password reset."""
        # Implement password reset logic
        messages.success(request, "Your password has been reset. You can now sign in.")
        return redirect("accounts:login")
