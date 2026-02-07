# Engineering Baseline

This document defines the baseline standards for architecture, coding practices, documentation, and collaboration. It is the source of truth for project-wide rules.

> **Version Reference**: See [`docs/TECH_STACK.md`](TECH_STACK.md) for exact versions of all dependencies.

## Guiding Principles

1. **Async-first**: Non-blocking by default; use sync only when necessary.
2. **Domain-driven**: Clean/Hexagonal architecture with Django conventions.
3. **Production-ready**: Security, reliability, and scalability are baseline requirements.
4. **Observable**: Structured logging, correlation IDs, and health checks from day one.
5. **Testable**: All code must be testable; coverage targets enforced in CI.
6. **Accessible**: WCAG 2.1 AA compliance for all user interfaces.
7. **International-ready**: i18n/l10n support from the start.

## Domain Glossary

> **Note**: Expand this glossary during Phase 0 Discovery.

| Term | Definition |
|------|------------|
| **Tenant** | A customer account; all user data is scoped to a tenant |
| **Account** | A financial account (bank, wallet, cash) owned by a user |
| **Transaction** | A single financial movement (credit or debit) |
| **Inflow** | Money coming in (income, deposits, transfers in) |
| **Outflow** | Money going out (expenses, withdrawals, transfers out) |
| **Asset** | Something of value owned (property, investments, receivables) |
| **Liability** | Money owed to others (loans, credit cards, payables) |
| **Loan** | A specific liability with repayment schedule |
| **Balance** | Current amount in an account (calculated, not stored) |
| **Category** | User-defined or system classification for transactions |
| **Budget** | Spending limit for a category over a time period |
| **Recurring** | Scheduled transactions that repeat on a pattern |

## Product Context

- SaaS B2C finance management platform
- Multi-tenant with strict data isolation per customer account
- Web UI (Django templates), Mobile API (DRF), Real-time (Channels)
- Django Admin as first-class super-admin interface

> **Reference**: See [`docs/decision-log/0003-b2c-saas-requirements.md`](decision-log/0003-b2c-saas-requirements.md) for detailed B2C requirements.

## B2C SaaS Requirements

### User Lifecycle
| Stage | Requirements |
|-------|-------------|
| Registration | Email verification, terms acceptance |
| Onboarding | Guided setup, help resources |
| Active Use | Dashboard, notifications, data export |
| Deletion | Right to erasure, data export, account closure |

### Data Privacy (GDPR/CCPA)
- **Right to access**: User can export all their data
- **Right to rectification**: User can update personal data
- **Right to erasure**: User can delete account and all data
- **Right to portability**: Export in machine-readable format (JSON/CSV)
- **Consent management**: Track and honor user preferences

### Self-Service Requirements
- Password reset via email
- Email change with verification
- Data export capability
- Account deletion (soft delete → hard delete after grace period)
- Help documentation and FAQ

### Communication Channels
| Type | Channel | Opt-in Required |
|------|---------|-----------------|
| Transactional | Email | No (essential) |
| Notifications | In-app, Push | Configurable |
| Marketing | Email | Yes |

## Stack Baseline

| Layer | Technology | Version Constraint |
|-------|------------|-------------------|
| Runtime | Python | `>=3.12,<3.14` |
| Framework | Django LTS | `>=5.2,<5.3` |
| API | Django REST Framework | `>=3.16,<4.0` |
| API Docs | drf-spectacular | `>=0.28,<1.0` |
| WebSocket | Django Channels + Daphne | `>=4.3,<5.0` |
| Background | Celery | `>=5.6,<6.0` |
| Database | PostgreSQL | `>=16,<18` |
| Cache/Broker | Redis | `>=7.2,<8.0` |
| Auth (JWT) | djangorestframework-simplejwt | `>=5.5,<6.0` |

Full dependency list: [`pyproject.toml`](../pyproject.toml)

## Multi-Tenancy (B2C)

### Design
- Single database with `tenant_id` on all tenant-owned tables
- Each customer account is a tenant
- Tenant context derived from authenticated user's account

### Enforcement Rules
1. Every tenant-owned model includes `tenant_id` foreign key
2. Composite unique constraints include `tenant_id`
3. Base queryset manager filters by tenant automatically
4. No cross-tenant data access is ever permitted

### Isolation Checklist
- [ ] Tenant context established per request (web, API, admin, Channels)
- [ ] DRF viewsets/querysets scoped to tenant
- [ ] Django Admin querysets and FK choices restricted to tenant
- [ ] Channels consumers validate tenant in connection scope
- [ ] Celery tasks include tenant ID in payload; re-validate on execution
- [ ] Automated tests verify tenant isolation for read/write paths

## Architecture (Modular Monolith)

### Structure
```
modules/
  <module_name>/
    domain/         # Pure Python; no framework imports
    application/    # Use-cases, orchestration, repository interfaces
    infrastructure/ # Django ORM, repo implementations, integrations
    interfaces/     # DRF views, Channels consumers, CLI
```

### Dependency Rules
```
interfaces --> application --> domain
                    ^
infrastructure -----+
```

- `domain/` must have zero Django/DRF/Celery/Channels imports
- `infrastructure/` depends on `application/` and `domain/`
- `domain/` never depends on `infrastructure/`
- Import boundary checks enforced in CI via `import-linter`

### Outbox Pattern
1. Command handler persists domain change + outbox event in single transaction
2. Celery dispatcher polls and publishes outbox events
3. Consumers push websocket notifications or trigger side effects
4. Demo module required showing full outbox flow

## Django and Python Standards

### Code Style
- PEP 8 compliance enforced by Ruff
- Django coding style guidelines
- Black for formatting (line length: 88)
- Type hints required for public APIs

### Views
- Prefer class-based views
- Use async class-based views for I/O-bound operations
- Keep view logic thin; delegate to services

### Models
- Models handle persistence only
- Business logic in domain services
- Use transactions for multi-step writes
- Migrations: small, additive, reversible

## Async-First Rules

| Scenario | Approach |
|----------|----------|
| I/O-bound view | `async def` view |
| Database query in async context | `database_sync_to_async` |
| Sync-only library in async | `sync_to_async` |
| CPU-bound work | Celery task |
| Long-running I/O | Celery task |

Document any sync-only exceptions with justification.

## Background Tasks (Celery)

### When to Use
- Blocking or long-running operations
- Email/SMS/push notifications
- Report generation and exports
- Scheduled/periodic jobs
- External API calls that may timeout

### Requirements
- Tasks must be idempotent
- Include `tenant_id` in task payload
- Retry with exponential backoff for transient failures
- Log task ID and correlation ID

## Financial Data Rules

| Rule | Implementation |
|------|----------------|
| Money storage | `Decimal` (never `float`) |
| Currency | ISO 4217 code, stored explicitly |
| Rounding | Per-currency rules documented |
| Timestamps | Timezone-aware UTC |
| Immutability | Financial records are append-only |
| Corrections | Via adjustment transactions only |
| Idempotency | Required for all write APIs |

## API Standards (DRF)

### Versioning
- Base path: `/api/v1/`
- Major version in URL path
- OpenAPI schema at `/api/schema/`
- Interactive docs at `/api/docs/`

### Design
- RESTful resource naming
- Consistent error response shape
- Cursor-based pagination for large datasets
- Rate limiting on all endpoints

### Contracts
- OpenAPI schema is the contract (via drf-spectacular)
- Breaking changes require version bump
- Event schemas in `contracts/events/` (Pydantic models)
- Typed environment schema via pydantic-settings

## Authentication and Security

### Authentication Methods
| Surface | Method | Library |
|---------|--------|---------|
| Web UI | Session + CSRF | Django auth |
| Mobile/API | JWT | djangorestframework-simplejwt |
| WebSocket | JWT (initial handshake) | Channels + simplejwt |

### Password Policy
- Minimum 12 characters
- Argon2id hashing (via argon2-cffi)
- Password breach checking (optional)
- Account lockout after 5 failed attempts

### Session/Token Security
- Cookies: `Secure`, `HttpOnly`, `SameSite=Lax`
- JWT access token: 15-minute lifetime
- JWT refresh token: 7-day lifetime with rotation
- Refresh token blacklist on logout

### OAuth/Social
- Out of scope until after first production release

### MFA
- Optional for v1
- TOTP-based with recovery codes if implemented

## Django Admin

### Standards
- Treat as first-class product surface
- Custom list displays, filters, and inlines
- Align styling with main design system
- Audit trail for all admin actions
- Tenant-scoped querysets and FK choices

## Internationalization (i18n)

### Requirements
- All user-facing strings must be translatable
- Use Django's translation framework (`gettext_lazy`)
- Date, time, and number formatting per locale
- Currency display per user preference
- RTL layout support for future languages

### Implementation Rules

| Rule | Implementation |
|------|----------------|
| String extraction | `{% trans %}` in templates, `_()` in Python |
| Lazy translation | Use `gettext_lazy` for model fields, form labels |
| Pluralization | Use `ngettext` for count-dependent strings |
| Date/time | Use `django.utils.formats` or user timezone |
| Numbers | Use `django.utils.numberformat` |
| Currency | Display in user's preferred format, store in base currency |

### Locale Files
```
locale/
├── en/LC_MESSAGES/django.po    # English (default)
├── es/LC_MESSAGES/django.po    # Spanish
└── ...
```

### Translation Workflow
1. Mark strings for translation in code
2. Run `make messages` to extract strings
3. Translate `.po` files
4. Run `make compilemessages` to compile
5. Test each supported locale

### Initial Scope
- English (en) as default
- Additional languages added based on user demand
- All UI text, error messages, emails translatable

## Accessibility (a11y)

### Compliance Target
- **WCAG 2.1 Level AA** minimum for all user interfaces
- Test with screen readers (NVDA, VoiceOver)
- Keyboard-only navigation must work completely

### Requirements

| Category | Requirements |
|----------|--------------|
| **Perceivable** | Alt text for images, captions for video, sufficient color contrast (4.5:1 minimum) |
| **Operable** | Keyboard accessible, no keyboard traps, skip links, focus indicators visible |
| **Understandable** | Clear labels, error identification, consistent navigation |
| **Robust** | Valid HTML, ARIA used correctly, works with assistive tech |

### Implementation Rules

```html
<!-- Form inputs must have labels -->
<label for="email">Email Address</label>
<input type="email" id="email" name="email" required aria-describedby="email-help">
<span id="email-help">We'll never share your email.</span>

<!-- Interactive elements need roles and states -->
<button aria-expanded="false" aria-controls="menu">Menu</button>

<!-- Images need alt text -->
<img src="chart.png" alt="Monthly spending chart showing $2,400 total">

<!-- Skip link for keyboard users -->
<a href="#main-content" class="skip-link">Skip to main content</a>
```

### Color Contrast Requirements

| Element | Minimum Ratio |
|---------|---------------|
| Normal text | 4.5:1 |
| Large text (18px+ or 14px+ bold) | 3:1 |
| UI components and graphics | 3:1 |
| Focus indicators | 3:1 |

### Testing Checklist
- [ ] All pages pass WAVE or axe accessibility checker
- [ ] All functionality works with keyboard only
- [ ] All pages work with screen reader
- [ ] Color is not the only means of conveying information
- [ ] Focus order is logical
- [ ] Form errors are announced to screen readers
- [ ] Modals trap focus correctly
- [ ] Dynamic content updates announced (aria-live)

## SEO

### Requirements
- Semantic HTML5 structure
- Meaningful page titles (unique per page, <60 chars)
- Meta descriptions (<160 chars, compelling)
- Open Graph and Twitter Card tags
- Sitemap.xml (auto-generated)
- robots.txt with appropriate rules
- Canonical URLs to prevent duplicates
- No client-only rendering for SEO-critical pages

### Implementation

```html
<head>
    <title>{{ page_title }} | Django Finance</title>
    <meta name="description" content="{{ page_description }}">
    <link rel="canonical" href="{{ canonical_url }}">

    <!-- Open Graph -->
    <meta property="og:title" content="{{ page_title }}">
    <meta property="og:description" content="{{ page_description }}">
    <meta property="og:image" content="{{ og_image_url }}">
    <meta property="og:url" content="{{ canonical_url }}">
    <meta property="og:type" content="website">

    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{{ page_title }}">
    <meta name="twitter:description" content="{{ page_description }}">
</head>
```

### Structured Data
- Organization schema on homepage
- BreadcrumbList for navigation
- FAQPage for help sections

## Security and Privacy

### Data Protection
- TLS 1.2+ for all connections
- Encryption at rest (database/disk level)
- Secrets via environment variables or secrets manager
- Never commit secrets to version control

### Logging
- No PII in logs unless required for audit
- Financial amounts not logged in plaintext
- Request correlation IDs in all logs

### Audit
- `AuditEvent` model: append-only, access-controlled
- Retention policy defined per data type
- User data export/delete support (B2C compliance)

## Error Handling

### Principles
- Validate all external inputs at boundaries
- Fail fast with clear, actionable error messages
- Never swallow exceptions silently
- Log failures with context (minus PII)
- Consistent error response format across APIs

### Error Categories

| Category | HTTP Status | Retry | Log Level |
|----------|-------------|-------|-----------|
| Validation Error | 400 | No | INFO |
| Authentication Error | 401 | No | WARNING |
| Authorization Error | 403 | No | WARNING |
| Not Found | 404 | No | DEBUG |
| Conflict | 409 | No | INFO |
| Rate Limited | 429 | Yes (with backoff) | INFO |
| Server Error | 500 | Yes | ERROR |
| Service Unavailable | 503 | Yes | ERROR |

### Error Response Format

```python
# All API errors must follow this format
{
    "error": {
        "code": "VALIDATION_ERROR",          # Machine-readable code
        "message": "Validation failed",       # Human-readable summary
        "details": [                          # Field-level errors (optional)
            {
                "field": "amount",
                "code": "invalid",
                "message": "Amount must be positive"
            }
        ],
        "correlation_id": "uuid",             # For support/debugging
        "documentation_url": "https://..."    # Optional help link
    }
}
```

### Exception Hierarchy

```python
# Domain exceptions (in domain/exceptions.py)
class DomainError(Exception):
    """Base class for domain errors."""

class ValidationError(DomainError):
    """Input validation failed."""

class NotFoundError(DomainError):
    """Requested entity not found."""

class ConflictError(DomainError):
    """Operation conflicts with current state."""

class AuthorizationError(DomainError):
    """User not authorized for this action."""

# Application exceptions (in application/exceptions.py)
class ApplicationError(Exception):
    """Base class for application errors."""

class ExternalServiceError(ApplicationError):
    """External service call failed."""
```

### Error Handling Rules

| Rule | Implementation |
|------|----------------|
| Catch specific exceptions | Never use bare `except:` |
| Re-raise with context | `raise NewError("context") from original` |
| Log before raising | Log at appropriate level with correlation ID |
| Translate at boundaries | Convert domain errors to HTTP responses in views |
| No sensitive data | Never include passwords, tokens, or PII in errors |

## Observability

### Logging Rules

| Rule | Requirement |
|------|-------------|
| Format | Structured JSON via structlog |
| Correlation | Every log entry includes `correlation_id` |
| Tenant | Include `tenant_id` for tenant-scoped operations |
| Timestamps | ISO 8601 format, UTC timezone |
| No PII | Never log email, name, address, phone |
| No Secrets | Never log passwords, tokens, API keys |
| No Financial | Never log account numbers, amounts in plaintext |

### Log Levels

| Level | When to Use | Examples |
|-------|-------------|----------|
| DEBUG | Detailed diagnostic info | Query parameters, internal state |
| INFO | Normal operations | Request completed, task started |
| WARNING | Unexpected but handled | Retry attempted, deprecated API used |
| ERROR | Operation failed | Exception caught, external service down |
| CRITICAL | System unusable | Database connection lost, out of memory |

### Logging Examples

```python
import structlog

logger = structlog.get_logger()

# Good - structured with context
logger.info(
    "transaction_created",
    transaction_id=str(transaction.id),
    tenant_id=str(tenant_id),
    transaction_type=transaction.type,
    correlation_id=str(correlation_id),
)

# Good - error with context
logger.error(
    "payment_failed",
    error_code=e.code,
    tenant_id=str(tenant_id),
    correlation_id=str(correlation_id),
    exc_info=True,
)

# Bad - unstructured
logger.info(f"Created transaction {transaction.id} for user {user.email}")

# Bad - contains PII
logger.info("User registered", email=user.email, name=user.full_name)
```

### Health Checks
- `/health/` - basic liveness (returns 200 if app running)
- `/health/ready/` - readiness (checks DB, Redis, Celery)

### Metrics (Production)

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Request latency p50 | < 100ms | > 200ms |
| Request latency p95 | < 500ms | > 1s |
| Request latency p99 | < 1s | > 2s |
| Error rate (5xx) | < 0.1% | > 1% |
| Database query p95 | < 50ms | > 100ms |
| Celery queue depth | < 100 | > 1000 |
| Celery task failure rate | < 1% | > 5% |

### Error Tracking
- Sentry integration for production
- Source maps for frontend errors
- Alert on new error types
- Group similar errors automatically

## Testing Strategy

### Test Types
| Type | Location | Purpose |
|------|----------|---------|
| Unit | `tests/unit/` | Domain logic, services |
| Integration | `tests/integration/` | APIs, DB, Channels |
| E2E | `tests/e2e/` | Critical user journeys |

### Requirements
- Coverage target: 80% minimum
- All tests deterministic and isolated
- Celery tasks tested with `task_always_eager=True`
- Tenant isolation tests for all data access paths

### Required Test Coverage
- [ ] Health endpoints
- [ ] Authentication flows (web + API)
- [ ] WebSocket auth and notifications
- [ ] Outbox dispatch and consumption
- [ ] Celery task execution
- [ ] Tenant isolation (read/write)

## CI Pipeline

### Stages
1. **Lint**: Ruff, Black (check mode)
2. **Type Check**: mypy
3. **Security**: Bandit, gitleaks
4. **Test**: pytest with coverage
5. **Import Check**: import-linter
6. **Contract Check**: OpenAPI schema validation

### Make Targets
```makefile
make up              # Start all services
make down            # Stop all services
make migrate         # Run migrations
make test            # Run test suite
make test-cov        # Run tests with coverage
make lint            # Run linters
make lint-fix        # Run linters with auto-fix
make typecheck       # Run mypy
make import-check    # Check import boundaries
make contract-check  # Validate OpenAPI schema
make format          # Format code
make shell           # Django shell
make logs            # Tail service logs
```

## Code Quality Tools

| Tool | Purpose | Config |
|------|---------|--------|
| Black | Formatting | `pyproject.toml` |
| Ruff | Linting + isort | `pyproject.toml` |
| mypy | Type checking | `pyproject.toml` |
| pre-commit | Git hooks | `.pre-commit-config.yaml` |
| Bandit | Security linting | `pyproject.toml` |

## Git Workflow

### Branching
- Trunk-based development with short-lived feature branches
- Branch naming: `feat/<topic>`, `fix/<topic>`, `chore/<topic>`

### Commits
Conventional Commits format:
```
<type>(<scope>): <summary>

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`

Rules:
- Summary: imperative mood, max 72 chars, no trailing period
- Scope: module name or area affected
- Body: explain what and why, not how

### Pre-commit Hooks
Enforced via `.pre-commit-config.yaml`:
- Formatting (Black, Ruff)
- Linting (Ruff)
- Security (Bandit, gitleaks)
- Conventional commit message validation

## Code Review Rules

### Requirements
- All changes require at least one approval before merge
- Author cannot approve their own code
- CI must pass before merge
- No direct commits to `main` branch

### Review Checklist

| Category | Check |
|----------|-------|
| **Correctness** | Does the code do what it's supposed to do? |
| **Architecture** | Does it follow layer boundaries and module structure? |
| **Security** | No hardcoded secrets, SQL injection, XSS vulnerabilities? |
| **Tenant Isolation** | All queries scoped to tenant? |
| **Performance** | No N+1 queries, appropriate indexes? |
| **Testing** | Adequate test coverage for new code? |
| **Error Handling** | Errors handled and logged appropriately? |
| **Documentation** | Public APIs documented, complex logic explained? |
| **Conventions** | Follows naming and coding conventions? |

### Review SLAs

| PR Size | Review Within |
|---------|---------------|
| Small (< 100 lines) | 4 hours |
| Medium (100-500 lines) | 1 business day |
| Large (> 500 lines) | Consider splitting |

### Merge Rules
- Squash merge for feature branches (clean history)
- Merge commit for release branches (preserve history)
- Delete branch after merge
- Update CHANGELOG.md for user-facing changes

## Database Migration Rules

### Principles
- Migrations must be **backwards compatible**
- Migrations must be **reversible** when possible
- Migrations must be **small and focused**
- No data migrations mixed with schema migrations

### Safe Migration Patterns

| Operation | Safe Pattern |
|-----------|--------------|
| Add column | Add with `null=True` or default value |
| Remove column | Deploy code first, then remove in next release |
| Rename column | Add new, copy data, deploy code, remove old |
| Add index | Use `CONCURRENTLY` for large tables |
| Change type | Create new column, migrate data, swap |

### Unsafe Operations (Require Review)

| Operation | Risk | Mitigation |
|-----------|------|------------|
| `NOT NULL` on existing column | Locks table | Add default, backfill, then constrain |
| Drop column | Breaks running code | Remove from code first |
| Rename table | Breaks queries | Use views for transition |
| Large data migration | Locks/timeout | Batch in Celery task |

### Migration Workflow

```bash
# 1. Create migration
python manage.py makemigrations <app>

# 2. Review SQL
python manage.py sqlmigrate <app> <migration_number>

# 3. Test locally
python manage.py migrate

# 4. Test rollback
python manage.py migrate <app> <previous_migration>

# 5. Commit and deploy
```

### Migration Naming
```
# Auto-generated (acceptable)
0001_initial.py
0002_user_email_verified.py

# Manual (descriptive)
0003_add_transaction_indexes.py
0004_backfill_currency_codes.py
```

## Dependency Management Rules

### Adding Dependencies

| Step | Action |
|------|--------|
| 1 | Justify the need (can stdlib do it?) |
| 2 | Check license compatibility (MIT, BSD, Apache OK) |
| 3 | Check maintenance status (recent commits, issues addressed) |
| 4 | Check security history (known vulnerabilities) |
| 5 | Add to `pyproject.toml` with version constraint |
| 6 | Update lock file |
| 7 | Document in PR why dependency was added |

### Version Constraints

| Dependency Type | Constraint | Example |
|-----------------|------------|---------|
| Framework (Django) | Pin to minor | `>=5.2,<5.3` |
| Library (stable) | Compatible release | `>=3.16,<4.0` |
| Library (fast-moving) | Minimum version | `>=0.28` |
| Dev tools | Minimum version | `>=24.10` |

### Updating Dependencies

| Frequency | Action |
|-----------|--------|
| Weekly | Review Dependabot/Renovate PRs |
| Monthly | Run `pip-audit` for vulnerabilities |
| Quarterly | Review all dependencies for updates |
| Immediately | Security patches for critical vulnerabilities |

### Forbidden Dependencies
- Dependencies with GPL/AGPL license (unless project is GPL)
- Unmaintained packages (no commits in 2+ years)
- Packages with unresolved critical CVEs

## Performance Rules

### Response Time Targets

| Endpoint Type | p50 Target | p95 Target |
|---------------|------------|------------|
| Health check | < 10ms | < 50ms |
| API read | < 100ms | < 300ms |
| API write | < 200ms | < 500ms |
| Page render | < 200ms | < 500ms |
| Report generation | < 2s | < 5s (or async) |

### Database Rules

| Rule | Implementation |
|------|----------------|
| No N+1 queries | Use `select_related()`, `prefetch_related()` |
| Index foreign keys | All FKs have indexes |
| Limit result sets | Always paginate, max 100 per page |
| Avoid `SELECT *` | Use `.only()` or `.values()` for large tables |
| Monitor slow queries | Log queries > 100ms |

### Caching Strategy

| Data Type | Cache Duration | Cache Location |
|-----------|----------------|----------------|
| User session | 2 weeks | Redis |
| API response (list) | 1 minute | Redis |
| Static config | 1 hour | Local memory + Redis |
| Computed aggregates | 5 minutes | Redis |
| Never cache | User-specific financial data | - |

### Background Task Rules

| Rule | Rationale |
|------|-----------|
| Offload > 500ms operations | Keep responses fast |
| Offload external API calls | Prevent timeout cascades |
| Offload email/notifications | Don't block user actions |
| Offload report generation | CPU-intensive |
| Offload batch operations | Prevent request timeout |

## Environment Rules

### Environment Definitions

| Environment | Purpose | Data | Access |
|-------------|---------|------|--------|
| Local | Development | Seed/fake data | Developer |
| Test | CI/automated tests | Generated fixtures | CI system |
| Staging | Pre-production testing | Anonymized production | Team |
| Production | Live users | Real data | Restricted |

### Environment Promotion

```
Local → Test (CI) → Staging → Production
         ↓
    All tests pass
         ↓
    Manual QA on staging
         ↓
    Production deploy
```

### Environment Rules

| Rule | Requirement |
|------|-------------|
| No production data locally | Use seed data or anonymized exports |
| Staging mirrors production | Same infrastructure, different scale |
| Environment parity | Same OS, Python version, dependencies |
| Secrets per environment | Never share secrets across environments |
| Feature flags | Test in staging before production |

## Feature Flag Rules

### When to Use Feature Flags

| Scenario | Use Flag |
|----------|----------|
| Gradual rollout | Yes |
| A/B testing | Yes |
| Kill switch for risky feature | Yes |
| Long-running feature branch | Yes |
| Simple bug fix | No |
| Config change | No (use env vars) |

### Feature Flag Structure

```python
FEATURE_FLAGS = {
    "feature_name": {
        "enabled": True,                    # Master switch
        "rollout_percentage": 25,           # % of users
        "user_segments": ["beta"],          # Specific segments
        "tenant_ids": ["uuid1", "uuid2"],   # Specific tenants
        "start_date": "2026-02-01",         # Auto-enable date
        "end_date": "2026-03-01",           # Auto-disable date
    }
}
```

### Feature Flag Lifecycle

| Stage | Duration | Action |
|-------|----------|--------|
| Created | Day 1 | Flag added, disabled |
| Testing | Week 1-2 | Enabled for internal/beta |
| Rollout | Week 2-4 | Gradual % increase |
| Full release | Week 4+ | 100% enabled |
| Cleanup | +2 weeks | Remove flag, keep feature |

### Rules
- Feature flags must have owners
- Remove flags within 30 days of full rollout
- Document all active flags
- Monitor flag usage in analytics

## Documentation Policy

### Required Updates
| Change Type | Update |
|-------------|--------|
| New feature | CHANGELOG.md |
| Architecture change | ENGINEERING_BASELINE.md, ADR |
| API change | OpenAPI schema |
| Security change | security.md, ADR |
| Config change | .env.example |

### Architecture Decision Records
- Location: `docs/decision-log/`
- Naming: `NNNN-title.md`
- Required for structural, technology, or security decisions

## AI Usage Policy

1. AI assistants must follow this baseline, project plan, and all documentation
2. AI-assisted changes require CHANGELOG.md updates
3. AI outputs must not bypass coding standards or architecture constraints
4. Human review required for security-sensitive changes
5. AI-generated code must pass all CI checks

## Review Checklist

Before merging any change:

- [ ] Async usage is appropriate and non-blocking
- [ ] Domain logic is decoupled from framework
- [ ] Tenant isolation maintained
- [ ] Tests added/updated with adequate coverage
- [ ] No PII or secrets in logs/responses
- [ ] Admin UI remains consistent (if applicable)
- [ ] SEO/accessibility maintained (if applicable)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] All CI checks pass
