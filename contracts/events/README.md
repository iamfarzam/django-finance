# Event Contracts

This directory contains event schema definitions using Pydantic models.

> **Reference**: See [`docs/ENGINEERING_BASELINE.md`](../../docs/ENGINEERING_BASELINE.md) for API and event contract standards.

## Structure

```
events/
  __init__.py
  base.py             # BaseEvent class with common fields
  accounts/
    __init__.py
    user_created.py
    user_updated.py
  finance/
    __init__.py
    transaction_created.py
    balance_updated.py
  notifications/
    __init__.py
    notification_sent.py
```

## Base Event

All events extend `BaseEvent`:

```python
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

class BaseEvent(BaseModel):
    event_id: UUID
    event_type: str
    event_version: str = "1.0"
    occurred_at: datetime
    correlation_id: UUID
    tenant_id: UUID
    actor_id: UUID | None = None
```

## Naming Convention

Event type format: `<domain>.<entity>.<action>`

Examples:
- `accounts.user.created`
- `accounts.user.email_verified`
- `finance.transaction.created`
- `finance.balance.updated`

## Validation

- Events are validated on publish (before writing to outbox)
- Events are validated on consume (before processing)
- Invalid events are logged and rejected
- Schema changes must be backward-compatible
