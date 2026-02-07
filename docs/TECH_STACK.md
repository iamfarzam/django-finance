# Tech Stack

This document is the **source of truth** for all technology choices, versions, and compatibility requirements. All dependencies must align with this specification.

Last updated: 2026-02-07

## Version Matrix

### Runtime

| Component | Version | Constraint | Support Until | Rationale |
|-----------|---------|------------|---------------|-----------|
| Python | 3.12.x | `>=3.12,<3.14` | Oct 2028 | LTS-equivalent; Django 5.2 compatible; stable async support |
| Django | 5.2.x LTS | `>=5.2,<5.3` | Apr 2028 | Long-term support; ASGI native; latest security patches |

### Web Framework & API

| Component | Version | Constraint | Rationale |
|-----------|---------|------------|-----------|
| Django REST Framework | 3.16.x | `>=3.16,<4.0` | Django 5.2 support; stable API |
| drf-spectacular | 0.28.x | `>=0.28,<1.0` | OpenAPI 3.1 support; active maintenance |
| Django Channels | 4.3.x | `>=4.3,<5.0` | WebSocket support; Django 5.2 compatible |
| Daphne | 4.1.x | `>=4.1,<5.0` | Production ASGI server; Channels integration |

### Authentication & Security

| Component | Version | Constraint | Rationale |
|-----------|---------|------------|-----------|
| djangorestframework-simplejwt | 5.5.x | `>=5.5,<6.0` | JWT for API/mobile; Django 5.2 support |
| argon2-cffi | 23.1.x | `>=23.1` | Argon2 password hashing (Django recommendation) |
| django-cors-headers | 4.6.x | `>=4.6,<5.0` | CORS for mobile API access |

### Background Tasks

| Component | Version | Constraint | Rationale |
|-----------|---------|------------|-----------|
| Celery | 5.6.x | `>=5.6,<6.0` | Background task processing; Python 3.12 support |
| django-celery-beat | 2.7.x | `>=2.7,<3.0` | Periodic task scheduling |
| django-celery-results | 2.5.x | `>=2.5,<3.0` | Task result backend |

### Database & Cache

| Component | Version | Constraint | Support Until | Rationale |
|-----------|---------|------------|---------------|-----------|
| PostgreSQL | 16.x | `>=16,<18` | Nov 2028 | LTS; Django 5.2 tested; production stable |
| psycopg | 3.2.x | `>=3.2,<4.0` | - | Async support; psycopg3 is the modern driver |
| Redis | 7.2.x | `>=7.2,<8.0` | - | BSD licensed; LTS; stable for cache/broker |
| django-redis | 5.4.x | `>=5.4,<6.0` | - | Django cache backend for Redis |
| redis (Python) | 5.2.x | `>=5.2,<6.0` | - | Python Redis client |

> **Note on Redis 8.x**: Redis 8.0+ changed to RSALv2/SSPLv1/AGPLv3 licensing. We use Redis 7.2.x (BSD licensed) for licensing clarity. Valkey is a BSD-licensed fork if Redis 7.x becomes unavailable.

### Configuration & Environment

| Component | Version | Constraint | Rationale |
|-----------|---------|------------|-----------|
| pydantic-settings | 2.7.x | `>=2.7,<3.0` | Typed environment configuration |
| pydantic | 2.10.x | `>=2.10,<3.0` | Data validation; settings foundation |

### Development & Testing

| Component | Version | Constraint | Rationale |
|-----------|---------|------------|-----------|
| pytest | 8.3.x | `>=8.3,<9.0` | Testing framework |
| pytest-django | 4.9.x | `>=4.9,<5.0` | Django test integration |
| pytest-asyncio | 0.24.x | `>=0.24,<1.0` | Async test support |
| pytest-cov | 6.0.x | `>=6.0,<7.0` | Coverage reporting |
| factory-boy | 3.3.x | `>=3.3,<4.0` | Test fixtures |
| httpx | 0.28.x | `>=0.28,<1.0` | Async HTTP testing client |

### Code Quality

| Component | Version | Constraint | Rationale |
|-----------|---------|------------|-----------|
| black | 24.10.x | `>=24.10` | Code formatting |
| ruff | 0.9.x | `>=0.9` | Fast linting (replaces flake8, isort, etc.) |
| mypy | 1.14.x | `>=1.14` | Static type checking |
| django-stubs | 5.1.x | `>=5.1` | Django type stubs for mypy |
| djangorestframework-stubs | 3.15.x | `>=3.15` | DRF type stubs |
| pre-commit | 4.0.x | `>=4.0` | Git hooks management |

### Infrastructure

| Component | Version | Constraint | Rationale |
|-----------|---------|------------|-----------|
| Docker | 27.x | `>=27` | Container runtime |
| Docker Compose | 2.32.x | `>=2.32` | Multi-container orchestration |
| gunicorn | 23.0.x | `>=23.0,<24.0` | Production WSGI (fallback) |

### Observability

| Component | Version | Constraint | Rationale |
|-----------|---------|------------|-----------|
| structlog | 24.4.x | `>=24.4,<25.0` | Structured logging |
| sentry-sdk | 2.19.x | `>=2.19,<3.0` | Error tracking (optional) |

## Compatibility Matrix

```
Python 3.12.x
    └── Django 5.2.x LTS
            ├── Django REST Framework 3.16.x
            │       └── drf-spectacular 0.28.x
            │       └── djangorestframework-simplejwt 5.5.x
            ├── Django Channels 4.3.x
            │       └── Daphne 4.1.x
            ├── Celery 5.6.x
            │       ├── django-celery-beat 2.7.x
            │       └── django-celery-results 2.5.x
            └── psycopg 3.2.x (PostgreSQL 16.x)
```

## Version Pinning Strategy

### Production Dependencies
- Use **compatible release** constraints: `>=X.Y,<X+1.0` or `~=X.Y`
- Pin to minor versions for stability
- Update quarterly or for security patches

### Development Dependencies
- Use **minimum version** constraints: `>=X.Y`
- Allow more flexibility for tooling updates

### Lock File
- Use `uv.lock` or `pip-tools` (requirements.txt) for reproducible builds
- Regenerate lock file on dependency updates
- Commit lock file to version control

## Infrastructure Requirements

### PostgreSQL 16.x
- Extensions required: `uuid-ossp`, `pg_trgm`
- Recommended settings:
  - `max_connections`: 100+ (adjust for connection pooling)
  - `shared_buffers`: 25% of RAM
  - `effective_cache_size`: 75% of RAM
- Backup: Daily automated backups with point-in-time recovery

### Redis 7.2.x
- Purpose: Cache, Celery broker, Channels layer
- Memory policy: `allkeys-lru` for cache, `noeviction` for broker
- Persistence: RDB snapshots for cache, AOF for broker (if durability needed)
- Recommended: Separate instances for cache vs. broker in production

### Container Base Images
- Python: `python:3.12-slim-bookworm`
- PostgreSQL: `postgres:16-bookworm`
- Redis: `redis:7.2-bookworm`

## Security Considerations

### Password Hashing
- Default: Argon2id via `argon2-cffi`
- Django setting: `PASSWORD_HASHERS` with Argon2 first

### JWT Configuration
- Access token lifetime: 15 minutes
- Refresh token lifetime: 7 days
- Rotation: Enabled (new refresh token on each use)
- Blacklist: Enabled for logout/revocation

### TLS/SSL
- Minimum TLS 1.2 for all connections
- PostgreSQL: `sslmode=require` in production
- Redis: TLS in production if network is untrusted

## Upgrade Policy

### LTS Alignment
- Django: Follow LTS releases (5.2 until Apr 2028)
- PostgreSQL: Stay within supported versions (5-year support)
- Python: Stay within security support window

### Quarterly Review
1. Check for security advisories
2. Review dependency updates
3. Test in staging environment
4. Update lock files
5. Deploy with rollback plan

## References

- [Django 5.2 Release Notes](https://docs.djangoproject.com/en/5.2/releases/5.2/)
- [Django Supported Versions](https://www.djangoproject.com/download/)
- [Python Status of Versions](https://devguide.python.org/versions/)
- [PostgreSQL Versioning Policy](https://www.postgresql.org/support/versioning/)
- [Redis Downloads](https://redis.io/downloads/)
- [Celery Changelog](https://docs.celeryq.dev/en/stable/changelog.html)
