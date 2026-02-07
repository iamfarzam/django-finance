# Contracts

This directory contains the source of truth for all system contracts.

> **Reference**: See [`docs/ENGINEERING_BASELINE.md`](../docs/ENGINEERING_BASELINE.md) for API standards and contract specifications.

## Overview

| Contract Type | Location | Format |
|--------------|----------|--------|
| REST API | Generated via drf-spectacular | OpenAPI 3.1 |
| Events | `contracts/events/` | Pydantic models |
| Settings | `pydantic-settings` | Python dataclass |

## REST API Contract

- **Base path**: `/api/v1/`
- **Schema**: `/api/schema/` (JSON), `/api/schema.yaml` (YAML)
- **Documentation**: `/api/docs/` (Swagger UI), `/api/redoc/` (ReDoc)
- **Versioning**: Major version in URL path

## Event Contracts

Event schemas are defined in `contracts/events/` using Pydantic models.

```
contracts/
  events/
    __init__.py
    base.py           # BaseEvent class
    accounts/         # Account-related events
    finance/          # Financial events
    notifications/    # Notification events
```

All events extend `BaseEvent` and are validated on publish and consume.

## Settings Contract

Environment configuration is managed via `pydantic-settings`:
- Schema defined in `config/settings.py`
- Template in `.env.example`
- Validated at application startup
