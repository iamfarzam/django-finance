# Modules

This directory contains all feature modules following the Clean/Hexagonal architecture pattern.

> **Reference**: See [`docs/ENGINEERING_BASELINE.md`](../docs/ENGINEERING_BASELINE.md) for architecture guidelines and [`docs/conventions.md`](../docs/conventions.md) for naming conventions.

## Structure

Each module is a vertical slice containing all layers:

```
modules/
  <module_name>/
    __init__.py
    domain/
      __init__.py
      entities.py       # Domain entities (pure Python dataclasses)
      value_objects.py  # Value objects (immutable)
      services.py       # Domain services
      events.py         # Domain events
      exceptions.py     # Domain-specific exceptions
    application/
      __init__.py
      use_cases.py      # Application use-cases
      commands.py       # Command handlers
      queries.py        # Query handlers
      interfaces.py     # Repository and service interfaces (ABCs)
      dto.py            # Data transfer objects
    infrastructure/
      __init__.py
      models.py         # Django ORM models
      repositories.py   # Repository implementations
      services.py       # External service implementations
      migrations/       # Database migrations
    interfaces/
      __init__.py
      views.py          # DRF viewsets/views
      serializers.py    # DRF serializers
      consumers.py      # Django Channels consumers
      urls.py           # URL configuration
```

## Layer Rules

### Domain Layer (`domain/`)
- **Pure Python only** - no Django, DRF, Celery, or Channels imports
- Contains business logic and rules
- Entities are the core business objects
- Value objects are immutable and compared by value
- Domain services contain logic that doesn't belong to a single entity

### Application Layer (`application/`)
- Orchestrates domain objects to perform use-cases
- Defines interfaces (abstract base classes) for infrastructure
- Handles transactions
- No direct database or external service calls

### Infrastructure Layer (`infrastructure/`)
- Implements interfaces defined in application layer
- Contains Django ORM models
- External service integrations
- Database migrations

### Interfaces Layer (`interfaces/`)
- HTTP/WebSocket entry points
- Request/response transformation
- Authentication and authorization checks
- DRF views and serializers
- Django Channels consumers

## Dependency Direction

```
interfaces --> application --> domain
                    ^
infrastructure -----+
```

- `domain/` must never import from `infrastructure/` or `interfaces/`
- `application/` depends only on `domain/`
- `infrastructure/` implements interfaces from `application/`
- `interfaces/` uses `application/` use-cases
- Import boundaries enforced in CI via `import-linter`

## Planned Modules

| Module | Purpose | Status |
|--------|---------|--------|
| `accounts` | User accounts, authentication, profiles | Planned |
| `tenants` | Multi-tenancy, tenant management | Planned |
| `finance` | Core financial entities (transactions, accounts) | Planned |
| `notifications` | Real-time and async notifications | Planned |
| `audit` | Audit logging and event tracking | Planned |
