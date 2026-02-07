"""Base event class for all domain events.

All events in the system inherit from BaseEvent and include
standard metadata fields for tracing and auditing.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import ClassVar
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


def _utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class BaseEvent(BaseModel):
    """Base class for all domain events.

    All events inherit from this class and include standard
    metadata for correlation, tracing, and auditing.

    Attributes:
        event_id: Unique identifier for this event instance.
        event_type: Fully qualified event type (e.g., "accounts.user.created").
        event_version: Schema version for backward compatibility.
        occurred_at: Timestamp when the event occurred.
        correlation_id: ID linking related events across services.
        tenant_id: Tenant context for multi-tenancy.
        actor_id: User or system that triggered the event.
    """

    model_config = ConfigDict(frozen=True)

    # Class-level configuration
    _event_type: ClassVar[str] = ""

    # Event metadata
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str = Field(default="")
    event_version: str = Field(default="1.0")
    occurred_at: datetime = Field(default_factory=_utc_now)
    correlation_id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    actor_id: UUID | None = None

    def model_post_init(self, __context: object) -> None:
        """Set event_type from class attribute if not provided."""
        if not self.event_type and self._event_type:
            object.__setattr__(self, "event_type", self._event_type)
