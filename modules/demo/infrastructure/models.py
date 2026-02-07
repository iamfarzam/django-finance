"""Models for the demo module.

Includes the Outbox model for implementing the outbox pattern.
"""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from django.db import models

from shared.models import BaseModel


class OutboxEvent(BaseModel):
    """Outbox event for reliable event publishing.

    The outbox pattern ensures events are published reliably by:
    1. Writing the event to the outbox table in the same transaction as the domain change
    2. A background worker polls and publishes events
    3. Events are marked as processed or retried on failure

    This provides at-least-once delivery semantics.
    """

    class Status(models.TextChoices):
        """Event status choices."""

        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        PROCESSED = "processed", "Processed"
        FAILED = "failed", "Failed"

    # Event metadata
    event_type = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Event type (e.g., 'accounts.user.created').",
    )
    event_id = models.UUIDField(
        db_index=True,
        help_text="Unique event identifier.",
    )
    correlation_id = models.UUIDField(
        db_index=True,
        help_text="Correlation ID for tracing.",
    )
    tenant_id = models.UUIDField(
        db_index=True,
        help_text="Tenant context for the event.",
    )

    # Event payload
    payload = models.JSONField(
        help_text="Event payload as JSON.",
    )

    # Processing status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    retry_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of processing attempts.",
    )
    max_retries = models.PositiveIntegerField(
        default=3,
        help_text="Maximum retry attempts.",
    )
    last_error = models.TextField(
        blank=True,
        help_text="Last processing error message.",
    )

    # Timestamps
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the event was successfully processed.",
    )
    scheduled_for = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="When to attempt processing (for retries).",
    )

    class Meta:
        db_table = "demo_outbox_events"
        verbose_name = "Outbox Event"
        verbose_name_plural = "Outbox Events"
        ordering = ["created_at"]
        indexes = [
            models.Index(
                fields=["status", "scheduled_for"],
                name="idx_outbox_status_scheduled",
            ),
            models.Index(
                fields=["event_type", "status"],
                name="idx_outbox_type_status",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.event_type} ({self.status})"

    @classmethod
    def create_from_event(
        cls,
        event: Any,
        tenant_id: UUID,
        correlation_id: UUID,
    ) -> "OutboxEvent":
        """Create an outbox entry from a domain event.

        Args:
            event: The domain event (Pydantic model).
            tenant_id: Tenant context.
            correlation_id: Correlation ID for tracing.

        Returns:
            Created OutboxEvent instance.
        """
        return cls.objects.create(
            event_type=event.event_type,
            event_id=event.event_id,
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            payload=json.loads(event.model_dump_json()),
        )

    def mark_processing(self) -> None:
        """Mark event as being processed."""
        self.status = self.Status.PROCESSING
        self.save(update_fields=["status", "updated_at"])

    def mark_processed(self) -> None:
        """Mark event as successfully processed."""
        from django.utils import timezone

        self.status = self.Status.PROCESSED
        self.processed_at = timezone.now()
        self.save(update_fields=["status", "processed_at", "updated_at"])

    def mark_failed(self, error: str) -> None:
        """Mark event as failed and schedule retry if applicable.

        Args:
            error: Error message to record.
        """
        from datetime import timedelta

        from django.utils import timezone

        self.retry_count += 1
        self.last_error = error

        if self.retry_count >= self.max_retries:
            self.status = self.Status.FAILED
        else:
            self.status = self.Status.PENDING
            # Exponential backoff: 1min, 2min, 4min, etc.
            delay = timedelta(minutes=2 ** (self.retry_count - 1))
            self.scheduled_for = timezone.now() + delay

        self.save(
            update_fields=[
                "status",
                "retry_count",
                "last_error",
                "scheduled_for",
                "updated_at",
            ]
        )


class Notification(BaseModel):
    """Notification model for real-time notifications."""

    class NotificationType(models.TextChoices):
        """Notification type choices."""

        INFO = "info", "Information"
        SUCCESS = "success", "Success"
        WARNING = "warning", "Warning"
        ERROR = "error", "Error"

    # Recipient
    user_id = models.UUIDField(
        db_index=True,
        help_text="User to notify.",
    )
    tenant_id = models.UUIDField(
        db_index=True,
        help_text="Tenant context.",
    )

    # Content
    title = models.CharField(
        max_length=255,
        help_text="Notification title.",
    )
    message = models.TextField(
        help_text="Notification message.",
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.INFO,
    )

    # Status
    is_read = models.BooleanField(
        default=False,
        db_index=True,
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    # Optional link
    action_url = models.URLField(
        blank=True,
        help_text="Optional action URL.",
    )

    class Meta:
        db_table = "demo_notifications"
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["user_id", "is_read", "-created_at"],
                name="idx_notification_user_read",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.notification_type})"

    def mark_as_read(self) -> None:
        """Mark notification as read."""
        from django.utils import timezone

        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=["is_read", "read_at", "updated_at"])
