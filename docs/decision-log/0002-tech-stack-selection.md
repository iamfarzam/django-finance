# ADR-0002: Tech Stack Selection

## Status
Accepted

## Date
2026-02-07

## Context

We are building a B2C SaaS finance management platform with the following requirements:

1. **Web application** with server-rendered pages (SEO important)
2. **Mobile API** for React Native client
3. **Real-time features** for live updates
4. **Background processing** for emails, reports, scheduled jobs
5. **Multi-tenant** with strict data isolation
6. **Financial data** requiring precision and auditability
7. **Production-ready** from inception

We need to select technologies that:
- Are stable and well-supported (LTS where available)
- Have strong async support for scalability
- Integrate well together
- Have active communities and documentation
- Support our security and compliance requirements

## Decision

### Runtime: Python 3.12
- **Constraint**: `>=3.12,<3.14`
- **Rationale**:
  - Latest stable with security support until Oct 2028
  - Django 5.2 fully compatible
  - Improved performance and error messages
  - Native type hint improvements
  - Stable async/await implementation

### Framework: Django 5.2 LTS
- **Constraint**: `>=5.2,<5.3`
- **Rationale**:
  - Long-term support until Apr 2028
  - Native ASGI support
  - Mature ecosystem
  - Excellent admin interface
  - Strong security track record
  - Large talent pool

### API: Django REST Framework 3.16
- **Constraint**: `>=3.16,<4.0`
- **Rationale**:
  - Industry standard for Django APIs
  - Excellent serialization
  - Built-in authentication
  - OpenAPI support via drf-spectacular
  - Active maintenance

### API Documentation: drf-spectacular
- **Constraint**: `>=0.28,<1.0`
- **Rationale**:
  - OpenAPI 3.1 support
  - Better than drf-yasg (no longer maintained)
  - Automatic schema generation
  - Swagger UI and ReDoc included

### WebSocket: Django Channels 4.3 + Daphne
- **Constraint**: `>=4.3,<5.0` (Channels), `>=4.1,<5.0` (Daphne)
- **Rationale**:
  - Official Django project
  - ASGI-native
  - Channel layers for scaling
  - Redis backend support

### Background Tasks: Celery 5.6
- **Constraint**: `>=5.6,<6.0`
- **Rationale**:
  - Industry standard for Python
  - Robust retry mechanisms
  - Scheduled tasks (beat)
  - Result backends
  - Monitoring tools (Flower)

### Database: PostgreSQL 16
- **Constraint**: `>=16,<18`
- **Rationale**:
  - 5-year support (until Nov 2028)
  - ACID compliance for financial data
  - JSON support for flexible schemas
  - Excellent Django integration
  - Row-level security for multi-tenancy
  - Extensions (uuid-ossp, pg_trgm)

### Cache/Broker: Redis 7.2
- **Constraint**: `>=7.2,<8.0`
- **Rationale**:
  - BSD licensed (7.x series)
  - LTS support
  - Celery broker
  - Django cache backend
  - Channels layer
  - Note: Redis 8.x changed to RSALv2/SSPLv1/AGPLv3; staying on 7.x for licensing clarity

### JWT Authentication: djangorestframework-simplejwt
- **Constraint**: `>=5.5,<6.0`
- **Rationale**:
  - Maintained by Jazzband
  - Token refresh/rotation
  - Blacklisting support
  - Django 5.2 compatible

### Password Hashing: Argon2 (argon2-cffi)
- **Constraint**: `>=23.1`
- **Rationale**:
  - OWASP recommended
  - Winner of Password Hashing Competition
  - Django's preferred hasher
  - Memory-hard (resistant to GPU attacks)

### Configuration: pydantic-settings
- **Constraint**: `>=2.7,<3.0`
- **Rationale**:
  - Type-safe configuration
  - Environment variable parsing
  - Validation at startup
  - Better than django-environ for type safety

### Logging: structlog
- **Constraint**: `>=24.4,<25.0`
- **Rationale**:
  - Structured JSON logging
  - Context binding
  - Processor pipeline
  - Works with stdlib logging

### Code Quality: Ruff + Black + mypy
- **Rationale**:
  - Ruff: Fast, replaces flake8/isort/many others
  - Black: Consistent formatting
  - mypy: Static type checking
  - All integrate with pre-commit

## Alternatives Considered

### FastAPI instead of Django
- **Rejected**: Need admin interface, ORM, mature ecosystem. FastAPI is excellent but Django provides more out-of-the-box for this use case.

### SQLAlchemy instead of Django ORM
- **Rejected**: Added complexity when Django ORM is sufficient. SQLAlchemy's flexibility isn't needed for our data model.

### RabbitMQ instead of Redis
- **Rejected**: Redis serves multiple purposes (cache, broker, channels). Single service is simpler to operate.

### Uvicorn instead of Daphne
- **Rejected**: Daphne is the official Django Channels server. Better integration and testing.

### Flask/Quart
- **Rejected**: Less batteries included. Would need to assemble components Django provides.

## Consequences

### Positive
- LTS alignment provides 2+ year stability window
- Strong async support throughout stack
- Well-documented, widely-used technologies
- Large talent pool for hiring
- Active maintenance and security patches

### Negative
- Django's ORM is synchronous (mitigated with `database_sync_to_async`)
- Learning curve for developers new to async Django
- Redis 7.x may eventually need migration to Valkey or Redis 8.x

### Risks
- PostgreSQL major upgrades require planning
- Celery can be complex to debug
- Must monitor for security advisories in all dependencies

## References

- [Django 5.2 Release Notes](https://docs.djangoproject.com/en/5.2/releases/5.2/)
- [Python Status of Versions](https://devguide.python.org/versions/)
- [PostgreSQL Versioning Policy](https://www.postgresql.org/support/versioning/)
- [Redis Licensing Change](https://redis.io/blog/redis-adopts-dual-source-available-licensing/)
- [OWASP Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
