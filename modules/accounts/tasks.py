"""Celery tasks for the accounts module.

Handles email sending for authentication flows.
"""

from __future__ import annotations

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

import structlog

logger = structlog.get_logger()


@shared_task(name="accounts.send_verification_email")
def send_verification_email(
    user_id: str,
    email: str,
    token: str,
    first_name: str = "",
) -> bool:
    """Send email verification link to user.

    Args:
        user_id: The user's ID for logging.
        email: The email address to send to.
        token: The verification token.
        first_name: User's first name for personalization.

    Returns:
        True if email was sent successfully.
    """
    verification_url = f"{settings.SITE_URL}/accounts/verify-email/?token={token}"

    subject = "Verify your email - Django Finance"

    # Plain text message
    message = f"""
Hi {first_name or 'there'},

Thank you for registering with Django Finance!

Please verify your email address by clicking the link below:

{verification_url}

This link will expire in 24 hours.

If you didn't create an account, you can safely ignore this email.

Best regards,
The Django Finance Team
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        logger.info(
            "verification_email_sent",
            user_id=user_id,
            email=email,
        )
        return True

    except Exception as e:
        logger.error(
            "verification_email_failed",
            user_id=user_id,
            email=email,
            error=str(e),
            exc_info=True,
        )
        raise


@shared_task(name="accounts.send_password_reset_email")
def send_password_reset_email(
    user_id: str,
    email: str,
    token: str,
    first_name: str = "",
) -> bool:
    """Send password reset link to user.

    Args:
        user_id: The user's ID for logging.
        email: The email address to send to.
        token: The password reset token.
        first_name: User's first name for personalization.

    Returns:
        True if email was sent successfully.
    """
    reset_url = f"{settings.SITE_URL}/accounts/reset-password/?token={token}"

    subject = "Reset your password - Django Finance"

    message = f"""
Hi {first_name or 'there'},

We received a request to reset your password for your Django Finance account.

Click the link below to reset your password:

{reset_url}

This link will expire in 1 hour.

If you didn't request a password reset, you can safely ignore this email.
Your password will remain unchanged.

Best regards,
The Django Finance Team
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        logger.info(
            "password_reset_email_sent",
            user_id=user_id,
            email=email,
        )
        return True

    except Exception as e:
        logger.error(
            "password_reset_email_failed",
            user_id=user_id,
            email=email,
            error=str(e),
            exc_info=True,
        )
        raise


@shared_task(name="accounts.send_password_changed_notification")
def send_password_changed_notification(
    user_id: str,
    email: str,
    first_name: str = "",
) -> bool:
    """Send password change notification to user.

    Args:
        user_id: The user's ID for logging.
        email: The email address to send to.
        first_name: User's first name for personalization.

    Returns:
        True if email was sent successfully.
    """
    subject = "Your password has been changed - Django Finance"

    message = f"""
Hi {first_name or 'there'},

This is a confirmation that the password for your Django Finance account
was recently changed.

If you made this change, you can safely ignore this email.

If you did NOT change your password, please contact our support team
immediately as your account may have been compromised.

Best regards,
The Django Finance Team
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        logger.info(
            "password_changed_notification_sent",
            user_id=user_id,
            email=email,
        )
        return True

    except Exception as e:
        logger.error(
            "password_changed_notification_failed",
            user_id=user_id,
            email=email,
            error=str(e),
            exc_info=True,
        )
        raise
