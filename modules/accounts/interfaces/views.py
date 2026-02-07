"""DRF views for the accounts module."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.utils import timezone
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from modules.accounts.domain.services import TokenGenerator
from modules.accounts.infrastructure.models import (
    EmailVerificationToken,
    PasswordResetToken,
    RefreshTokenBlacklist,
    User,
)
from modules.accounts.interfaces.serializers import (
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
    RegisterSerializer,
    RequestPasswordResetSerializer,
    ResetPasswordSerializer,
    UpdateProfileSerializer,
    UserSerializer,
    VerifyEmailSerializer,
)
from modules.accounts.interfaces.throttling import (
    ChangePasswordRateThrottle,
    LoginRateThrottle,
    PasswordResetRateThrottle,
    RegisterRateThrottle,
    ResendVerificationRateThrottle,
    VerifyEmailRateThrottle,
)


class RegisterView(GenericAPIView):
    """User registration endpoint."""

    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer
    throttle_classes = [RegisterRateThrottle]

    def post(self, request: Request) -> Response:
        """Register a new user.

        Creates a new user account and sends a verification email.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Create verification token
        token = TokenGenerator.generate_verification_token()
        EmailVerificationToken.objects.create(
            user=user,
            email=user.email,
            token=token,
            expires_at=timezone.now() + timedelta(hours=24),
        )

        # TODO: Send verification email via Celery task

        return Response(
            {
                "message": "Registration successful. Please check your email to verify your account.",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    """JWT login endpoint."""

    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [LoginRateThrottle]


class RefreshTokenView(TokenRefreshView):
    """JWT token refresh endpoint."""

    pass


class LogoutView(APIView):
    """Logout endpoint that blacklists the refresh token."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        """Logout user by blacklisting refresh token."""
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"error": {"code": "MISSING_TOKEN", "message": "Refresh token is required."}},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            token = RefreshToken(refresh_token)

            # Blacklist the token
            RefreshTokenBlacklist.objects.create(
                token_jti=token["jti"],
                user=request.user,
                expires_at=timezone.now() + timedelta(days=7),
            )

            return Response({"message": "Successfully logged out."})
        except TokenError:
            return Response(
                {"error": {"code": "INVALID_TOKEN", "message": "Invalid token."}},
                status=status.HTTP_400_BAD_REQUEST,
            )


class VerifyEmailView(GenericAPIView):
    """Email verification endpoint."""

    permission_classes = [AllowAny]
    serializer_class = VerifyEmailSerializer
    throttle_classes = [VerifyEmailRateThrottle]

    def post(self, request: Request) -> Response:
        """Verify user email with token."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token_str = serializer.validated_data["token"]

        try:
            token = EmailVerificationToken.objects.get(token=token_str)
        except EmailVerificationToken.DoesNotExist:
            return Response(
                {"error": {"code": "INVALID_TOKEN", "message": "Invalid verification token."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not token.is_valid:
            return Response(
                {"error": {"code": "TOKEN_EXPIRED", "message": "Verification token has expired."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify user email
        user = token.user
        user.verify_email()

        # Mark token as used
        token.used_at = timezone.now()
        token.save(update_fields=["used_at"])

        return Response(
            {
                "message": "Email verified successfully.",
                "user": UserSerializer(user).data,
            }
        )


class ResendVerificationView(APIView):
    """Resend email verification endpoint."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [ResendVerificationRateThrottle]

    def post(self, request: Request) -> Response:
        """Resend verification email."""
        user = request.user

        if user.is_email_verified:
            return Response(
                {"error": {"code": "ALREADY_VERIFIED", "message": "Email is already verified."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Invalidate existing tokens
        EmailVerificationToken.objects.filter(user=user, used_at__isnull=True).update(
            used_at=timezone.now()
        )

        # Create new token
        token = TokenGenerator.generate_verification_token()
        EmailVerificationToken.objects.create(
            user=user,
            email=user.email,
            token=token,
            expires_at=timezone.now() + timedelta(hours=24),
        )

        # TODO: Send verification email via Celery task

        return Response({"message": "Verification email sent."})


class RequestPasswordResetView(GenericAPIView):
    """Password reset request endpoint."""

    permission_classes = [AllowAny]
    serializer_class = RequestPasswordResetSerializer
    throttle_classes = [PasswordResetRateThrottle]

    def post(self, request: Request) -> Response:
        """Request password reset email.

        Always returns success to prevent email enumeration.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].lower()

        try:
            user = User.objects.get(email__iexact=email)

            # Invalidate existing tokens
            PasswordResetToken.objects.filter(user=user, used_at__isnull=True).update(
                used_at=timezone.now()
            )

            # Create new token
            token = TokenGenerator.generate_password_reset_token()
            PasswordResetToken.objects.create(
                user=user,
                token=token,
                expires_at=timezone.now() + timedelta(hours=1),
            )

            # TODO: Send reset email via Celery task

        except User.DoesNotExist:
            # Don't reveal that user doesn't exist
            pass

        return Response(
            {"message": "If an account exists with this email, a password reset link has been sent."}
        )


class ResetPasswordView(GenericAPIView):
    """Password reset endpoint."""

    permission_classes = [AllowAny]
    serializer_class = ResetPasswordSerializer
    throttle_classes = [PasswordResetRateThrottle]

    def post(self, request: Request) -> Response:
        """Reset password with token."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token_str = serializer.validated_data["token"]
        new_password = serializer.validated_data["password"]

        try:
            token = PasswordResetToken.objects.get(token=token_str)
        except PasswordResetToken.DoesNotExist:
            return Response(
                {"error": {"code": "INVALID_TOKEN", "message": "Invalid reset token."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not token.is_valid:
            return Response(
                {"error": {"code": "TOKEN_EXPIRED", "message": "Reset token has expired."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update password
        user = token.user
        user.set_password(new_password)
        user.save()

        # Mark token as used
        token.used_at = timezone.now()
        token.save(update_fields=["used_at"])

        # Invalidate all refresh tokens for security
        RefreshTokenBlacklist.objects.bulk_create([
            RefreshTokenBlacklist(
                token_jti=f"password_reset_{user.id}_{timezone.now().timestamp()}",
                user=user,
                expires_at=timezone.now() + timedelta(days=7),
            )
        ])

        # TODO: Send password changed notification via Celery task

        return Response({"message": "Password reset successfully."})


class ChangePasswordView(GenericAPIView):
    """Change password endpoint for authenticated users."""

    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer
    throttle_classes = [ChangePasswordRateThrottle]

    def post(self, request: Request) -> Response:
        """Change user password."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        # TODO: Send password changed notification via Celery task

        return Response({"message": "Password changed successfully."})


class ProfileView(GenericAPIView):
    """User profile endpoint."""

    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get(self, request: Request) -> Response:
        """Get current user profile."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class UpdateProfileView(GenericAPIView):
    """Update user profile endpoint."""

    permission_classes = [IsAuthenticated]
    serializer_class = UpdateProfileSerializer

    def patch(self, request: Request) -> Response:
        """Update user profile."""
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(UserSerializer(request.user).data)
