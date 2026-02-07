"""Rate limiting configuration for authentication endpoints.

These throttle classes implement rate limiting to protect against
brute force attacks and abuse.
"""

from __future__ import annotations

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """Rate limit for login attempts.

    Limits login attempts per IP address to prevent brute force attacks.
    """

    scope = "login"
    rate = "5/minute"


class PasswordResetRateThrottle(AnonRateThrottle):
    """Rate limit for password reset requests.

    Limits password reset requests to prevent email bombing.
    """

    scope = "password_reset"
    rate = "3/hour"


class RegisterRateThrottle(AnonRateThrottle):
    """Rate limit for registration.

    Limits registration attempts to prevent spam accounts.
    """

    scope = "register"
    rate = "10/hour"


class VerifyEmailRateThrottle(AnonRateThrottle):
    """Rate limit for email verification.

    Limits verification attempts to prevent token enumeration.
    """

    scope = "verify_email"
    rate = "10/minute"


class ChangePasswordRateThrottle(UserRateThrottle):
    """Rate limit for password change.

    Limits password changes per authenticated user.
    """

    scope = "change_password"
    rate = "5/hour"


class ResendVerificationRateThrottle(UserRateThrottle):
    """Rate limit for resending verification emails.

    Limits verification email resends to prevent email bombing.
    """

    scope = "resend_verification"
    rate = "3/hour"
