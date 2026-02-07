# Project Plan

Created: 2026-02-07
Last Updated: 2026-02-08
Status: Active

## How to Use This Plan

1. Update this plan before starting a new phase or major initiative
2. Keep each phase status current (Not started | In progress | Done)
3. Log completed work in `docs/CHANGELOG.md`
4. After first production release, log maintenance changes in `docs/CHANGELOG.md` under the post-production section

## Vision

Build a production-ready, async-first finance management platform with a decoupled, domain-driven architecture that supports web, mobile, and real-time features while keeping SEO and admin usability as baseline requirements.

## Scope

| Feature | Technology |
|---------|------------|
| Cash flow tracking | Inflow, outflow, assets, liabilities, loans |
| Web application | Django templates (SSR) |
| Mobile API | Django REST Framework |
| Real-time updates | Django Channels + WebSocket |
| Admin interface | Django Admin (first-class) |
| Multi-tenancy | Single database, tenant-scoped |

## Phase Overview

| Phase | Name | Status |
|-------|------|--------|
| 0 | Discovery and Requirements | **Done** |
| 1 | Architecture and Baseline Standards | **Done** |
| 2 | Foundations | **Done** |
| 3 | Core Domain Modeling | **Done** |
| 4 | API and Integrations | **Done** |
| 5 | Real-time Features | Not started |
| 6 | Web UI | Not started |
| 7 | Admin Modernization | Not started |
| 8 | Optional React SSR Web | Not started |
| 9 | Production Readiness | Not started |
| 10 | Release and Maintenance | Not started |

---

## Phase 0: Discovery and Requirements
**Status**: Done
**Completed**: 2026-02-07

### Deliverables
- [x] Finalize the domain glossary and bounded contexts
- [x] Define user roles, permissions, and audit requirements
- [x] Finalize the account model and tenant boundaries (B2C)
- [x] Finalize multi-tenancy design (single database with tenant scoping)
- [x] Define the tenant context source (account ID, subdomain, or header)
- [x] Select and document infrastructure choices (database, cache/broker, object storage)
- [x] Finalize the authentication approach (no OAuth before first release)
- [x] Finalize data retention and privacy requirements
- [x] Finalize password policy and account recovery requirements
- [x] Finalize the accounting model and currency scope
- [x] Finalize data export/delete expectations (B2C)
- [x] Finalize audit log retention and access policies

### Key Decisions
- **User Roles**: Anonymous, User, Premium, SuperAdmin
- **Tenant Context**: JWT claim for API, session for web
- **Accounting Model**: Single-entry (simpler for B2C personal finance)
- **Audit Retention**: 7 years for financial/account, 2 years for security

---

## Phase 1: Architecture and Baseline Standards
**Status**: Done
**Completed**: 2026-02-07

### Deliverables

#### Core Documentation
- [x] Architecture outline for the modular monolith (Clean/Hex) defined
- [x] Engineering baseline documented (`docs/ENGINEERING_BASELINE.md`)
- [x] Tech stack version matrix established (`docs/TECH_STACK.md`)
- [x] B2C SaaS product baseline created (`docs/PRODUCT_BASELINE.md`)
- [x] Security baseline documented (`docs/security.md`)
- [x] Comprehensive naming and coding conventions (`docs/conventions.md`)
- [x] Project plan with phases (`docs/PLAN.md`)
- [x] Changelog established (`docs/CHANGELOG.md`)

#### Configuration Files
- [x] Project configuration created (`pyproject.toml`)
- [x] Pre-commit hooks configured (`.pre-commit-config.yaml`)
- [x] Environment template created (`.env.example`)
- [x] Makefile with development commands created

#### Architecture Decision Records
- [x] ADR process established under `docs/decision-log/`
- [x] Tech stack ADR created (`0002-tech-stack-selection.md`)
- [x] B2C SaaS requirements ADR created (`0003-b2c-saas-requirements.md`)

#### Rules and Regulations
- [x] Domain glossary with core business terms
- [x] Internationalization (i18n) requirements
- [x] Accessibility (a11y) WCAG 2.1 AA requirements
- [x] Error handling rules and patterns
- [x] Logging rules with examples
- [x] Code review rules and SLAs
- [x] Database migration rules
- [x] Dependency management rules
- [x] Performance rules with targets
- [x] Environment promotion rules
- [x] Feature flag lifecycle rules

### Key Decisions
- Python 3.12+ with Django 5.2 LTS
- PostgreSQL 16+ for database
- Redis 7.2+ for cache/broker (BSD licensed)
- Celery 5.6+ for background tasks
- JWT for API auth, sessions for web

---

## Phase 2: Foundations
**Status**: Done
**Completed**: 2026-02-08

### Prerequisites
- Phase 0 or Phase 1 complete
- Infrastructure decisions finalized

### Deliverables
- [x] Django project structure with ASGI, Channels, and Daphne
- [x] Settings split by environment (local, test, production)
- [x] Secrets handling via pydantic-settings
- [x] CI baseline (lint, formatting, tests, import-check, contract-check)
- [x] Docker and docker-compose configuration
- [x] Makefile with standard targets
- [x] Logging configuration with structlog
- [x] Health check endpoints (`/health/`, `/health/ready/`)
- [x] Error tracking setup (Sentry integration)
- [x] Celery setup with Redis broker
- [x] Authentication implementation:
  - [x] Web sessions with secure cookies
  - [x] JWT for API (access + refresh tokens)
  - [x] Email verification flow
- [x] Auth hardening:
  - [x] Rate limiting on login/recovery
  - [x] Account lockout thresholds
  - [x] Password policy enforcement
- [x] Session/JWT security settings
- [x] Tenant context middleware and propagation
- [x] Base tenant-aware model and manager
- [x] Demo module showing:
  - [x] JWT login flow
  - [x] WebSocket authentication
  - [x] Outbox pattern dispatch
  - [x] Real-time notification

### Key Components Created
- `config/` - Django configuration with environment-based settings
- `shared/` - Base models, middleware, exceptions, logging
- `modules/accounts/` - User authentication and management
- `modules/demo/` - Outbox pattern and WebSocket demos
- `contracts/events/` - Base event schema for domain events

---

## Phase 3: Core Domain Modeling
**Status**: Done
**Completed**: 2026-02-08

### Prerequisites
- Phase 2 complete

### Deliverables
- [x] Core domain entities:
  - [x] Account/Wallet
  - [x] Transaction (inflow/outflow)
  - [x] Asset
  - [x] Liability
  - [x] Loan
  - [x] Transfer (between accounts)
  - [x] Category (transaction classification)
- [x] Domain services and validation rules
- [x] Monetary precision and currency handling
- [x] Rounding policies documented
- [x] Accounting model implementation (single-entry)
- [x] Immutable financial records with adjustment workflows
- [x] Tenant scoping on all domain models
- [x] Idempotency key support for financial writes
- [x] Migration strategy and data integrity checks
- [x] Unit tests for domain logic

### Key Components Created
- `modules/finance/domain/` - Pure Python domain layer
  - `enums.py` - Transaction types, account types, asset types, etc.
  - `value_objects.py` - Money, Currency, IdempotencyKey, ExchangeRate
  - `entities.py` - Account, Transaction, Transfer, Asset, Liability, Loan, Category
  - `services.py` - BalanceCalculator, NetWorthCalculator, CashFlowAnalyzer
  - `events.py` - Domain events for all entities
  - `exceptions.py` - Domain-specific exceptions
- `modules/finance/application/` - Use cases and interfaces
  - `dto.py` - Data transfer objects for all entities
  - `interfaces.py` - Repository interfaces
  - `use_cases.py` - Application use cases
- `modules/finance/infrastructure/` - Django ORM layer
  - `models.py` - Django models with tenant scoping
  - `admin.py` - Django admin configuration
- `modules/finance/interfaces/` - API layer
  - `serializers.py` - DRF serializers
  - `views.py` - DRF viewsets
  - `urls.py` - API URL routing
- `tests/unit/finance/` - Unit tests for domain logic

### Technical Decisions
- Single-entry accounting (Amount positive, type determines direction)
- Currency support: USD, EUR, GBP, CAD, AUD, JPY, INR
- Decimal precision: 4 decimal places for storage, rounded per currency
- Rounding: ROUND_HALF_UP (banker's rounding)
- Balance calculated from transactions, not stored

---

## Phase 4: API and Integrations
**Status**: Done
**Completed**: 2026-02-08

### Prerequisites
- Phase 3 complete

### Deliverables
- [x] DRF API design and URL structure
- [x] API versioning (`/api/v1/`)
- [x] Standard serializers and validators
- [x] Permissions and authorization
- [x] Throttling configuration
- [x] Audit logging middleware
- [x] OpenAPI schema generation (drf-spectacular)
- [x] API documentation (`/api/docs/`)
- [x] Mobile client contract documentation
- [x] Integration tests for all endpoints

### Key Components Created
- `shared/permissions.py` - Role-based permission classes
  - `IsActiveUser`, `IsPremiumUser`, `IsSuperAdmin`
  - `IsOwner`, `TenantIsolation`, `CanCreateAccount`
- `shared/audit.py` - Audit logging service
  - `AuditAction` enum with all auditable actions
  - `AuditEvent` dataclass with context and changes
  - `AuditLogger` service for structured audit logging
- `shared/middleware.py` - Added `AuditLoggingMiddleware`
- `modules/finance/interfaces/throttling.py` - Finance-specific throttle classes
  - Transaction, transfer, account, report throttles
  - Premium user enhanced throttle limits
- `docs/api-documentation.md` - Comprehensive API documentation
- `tests/integration/test_finance_api.py` - Integration tests for all endpoints

### Technical Decisions
- Permissions use role-based access control (User, Premium, SuperAdmin)
- Account creation limited to 3 for basic users, unlimited for premium
- Audit logs use structured logging with correlation IDs
- Finance API throttle rates: 200/hour user, 1000/hour premium
- OpenAPI documentation with JWT security scheme

---

## Phase 5: Real-time Features
**Status**: Not started

### Prerequisites
- Phase 4 complete

### Deliverables
- [ ] Channels consumer implementation
- [ ] Event routing and groups
- [ ] WebSocket authentication
- [ ] Real-time balance updates
- [ ] Transaction notifications
- [ ] Backpressure handling
- [ ] Connection health monitoring
- [ ] Integration tests for WebSocket flows

---

## Phase 6: Web UI (Django Templates)
**Status**: Not started

### Prerequisites
- Phase 4 complete

### Deliverables
- [ ] Base templates and design system
- [ ] Authentication pages (login, register, password reset)
- [ ] Dashboard
- [ ] Transaction management pages
- [ ] Account/wallet views
- [ ] Asset and liability tracking
- [ ] SEO implementation:
  - [ ] Meta tags
  - [ ] Sitemaps
  - [ ] robots.txt
  - [ ] Open Graph tags
- [ ] Accessibility baseline (WCAG 2.1 AA)
- [ ] Responsive design

---

## Phase 7: Admin Modernization
**Status**: Not started

### Prerequisites
- Phase 6 complete

### Deliverables
- [ ] Custom admin branding
- [ ] Enhanced list displays and filters
- [ ] Inline editing for related models
- [ ] Financial entity management workflows
- [ ] Approval workflows (if needed)
- [ ] Admin permission review
- [ ] Audit trail visibility
- [ ] Admin documentation

---

## Phase 8: Optional React SSR Web
**Status**: Not started

### Prerequisites
- Phase 7 complete
- Decision to proceed with React SSR approved

### Deliverables
- [ ] React SSR setup (Next.js or similar)
- [ ] Shared design system between SSR and templates
- [ ] Component library
- [ ] API integration
- [ ] SEO parity with templates

---

## Phase 9: Production Readiness
**Status**: Not started

### Prerequisites
- Phase 7 (or 8 if applicable) complete

### Deliverables
- [ ] Performance testing and optimization
- [ ] Load testing results
- [ ] Security review and hardening
- [ ] Penetration testing (if required)
- [ ] Backup automation and restore testing
- [ ] Monitoring and alerting setup:
  - [ ] Uptime monitoring
  - [ ] Error rate alerts
  - [ ] Task backlog alerts
  - [ ] Database performance
- [ ] Initial SLO targets defined and reviewed
- [ ] Rollback procedure documented and tested
- [ ] Runbook updated for production operations
- [ ] Disaster recovery plan

---

## Phase 10: Release and Maintenance
**Status**: Not started

### Prerequisites
- Phase 9 complete

### Deliverables
- [ ] Release process documented
- [ ] Versioning rules established
- [ ] Changelog format finalized
- [ ] Maintenance logging process
- [ ] Long-term support policy
- [ ] First production release

---

## Dependencies

```
Phase 0 (Discovery)
    │
    ▼
Phase 1 (Baseline) ──────────────────┐
    │                                │
    ▼                                │
Phase 2 (Foundations)                │
    │                                │
    ▼                                │
Phase 3 (Domain)                     │
    │                                │
    ▼                                │
Phase 4 (API)                        │
    │                                │
    ├──────────────┐                 │
    ▼              ▼                 │
Phase 5        Phase 6               │
(Real-time)    (Web UI)              │
    │              │                 │
    └──────┬───────┘                 │
           ▼                         │
       Phase 7                       │
       (Admin)                       │
           │                         │
           ├─────────────────────────┤
           ▼                         │
       Phase 8 (optional)            │
       (React SSR)                   │
           │                         │
           ▼                         │
       Phase 9 ◄─────────────────────┘
       (Production)
           │
           ▼
       Phase 10
       (Release)
```

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Scope creep | Medium | High | Strict phase gating, change control |
| Technical debt | Medium | Medium | Regular refactoring, code review |
| Security vulnerability | Low | Critical | Security reviews, dependency scanning |
| Performance issues | Medium | Medium | Load testing, profiling |
| Team knowledge gaps | Medium | Medium | Documentation, pair programming |
