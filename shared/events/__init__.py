"""Event handling infrastructure for real-time updates."""

from shared.events.handlers import (
    FinanceEventHandler,
    SocialEventHandler,
    register_event_handlers,
)

__all__ = [
    "FinanceEventHandler",
    "SocialEventHandler",
    "register_event_handlers",
]
