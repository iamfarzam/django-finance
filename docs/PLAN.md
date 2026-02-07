# Project Plan

Created: 2026-02-07
Last Updated: 2026-02-07
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
| 0 | Discovery and Requirements | Not started |
| 1 | Architecture and Baseline Standards | **Done** |
| 2 | Foundations | Not started |
| 3 | Core Domain Modeling | Not started |
| 4 | API and Integrations | Not started |
| 5 | Real-time Features | Not started |
| 6 | Web UI | Not started |
| 7 | Admin Modernization | Not started |
| 8 | Optional React SSR Web | Not started |
| 9 | Production Readiness | Not started |
| 10 | Release and Maintenance | Not started |

---

## Phase 0: Discovery and Requirements
**Status**: Not started

### Deliverables
- [ ] Finalize the domain glossary and bounded contexts
- [ ] Define user roles, permissions, and audit requirements
- [ ] Finalize the account model and tenant boundaries (B2C)
- [ ] Finalize multi-tenancy design (single database with tenant scoping)
- [ ] Define the tenant context source (account ID, subdomain, or header)
- [ ] Select and document infrastructure choices (database, cache/broker, object storage)
- [ ] Finalize the authentication approach (no OAuth before first release)
- [ ] Finalize data retention and privacy requirements
- [ ] Finalize password policy and account recovery requirements
- [ ] Finalize the accounting model and currency scope
- [ ] Finalize data export/delete expectations (B2C)
- [ ] Finalize audit log retention and access policies

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
**Status**: Not started

### Prerequisites
- Phase 0 or Phase 1 complete
- Infrastructure decisions finalized

### Deliverables
- [ ] Django project structure with ASGI, Channels, and Daphne
- [ ] Settings split by environment (local, test, production)
- [ ] Secrets handling via pydantic-settings
- [ ] CI baseline (lint, formatting, tests, import-check, contract-check)
- [ ] Docker and docker-compose configuration
- [ ] Makefile with standard targets
- [ ] Logging configuration with structlog
- [ ] Health check endpoints (`/health/`, `/health/ready/`)
- [ ] Error tracking setup (Sentry integration)
- [ ] Celery setup with Redis broker
- [ ] Authentication implementation:
  - [ ] Web sessions with secure cookies
  - [ ] JWT for API (access + refresh tokens)
  - [ ] Email verification flow
- [ ] Auth hardening:
  - [ ] Rate limiting on login/recovery
  - [ ] Account lockout thresholds
  - [ ] Password policy enforcement
- [ ] Session/JWT security settings
- [ ] Tenant context middleware and propagation
- [ ] Base tenant-aware model and manager
- [ ] Demo module showing:
  - [ ] JWT login flow
  - [ ] WebSocket authentication
  - [ ] Outbox pattern dispatch
  - [ ] Real-time notification

---

## Phase 3: Core Domain Modeling
**Status**: Not started

### Prerequisites
- Phase 2 complete

### Deliverables
- [ ] Core domain entities:
  - [ ] Account/Wallet
  - [ ] Transaction (inflow/outflow)
  - [ ] Asset
  - [ ] Liability
  - [ ] Loan
- [ ] Domain services and validation rules
- [ ] Monetary precision and currency handling
- [ ] Rounding policies documented
- [ ] Accounting model implementation (single-entry or ledger)
- [ ] Immutable financial records with adjustment workflows
- [ ] Tenant scoping on all domain models
- [ ] Idempotency key support for financial writes
- [ ] Migration strategy and data integrity checks
- [ ] Unit tests for domain logic

---

## Phase 4: API and Integrations
**Status**: Not started

### Prerequisites
- Phase 3 complete

### Deliverables
- [ ] DRF API design and URL structure
- [ ] API versioning (`/api/v1/`)
- [ ] Standard serializers and validators
- [ ] Permissions and authorization
- [ ] Throttling configuration
- [ ] Audit logging middleware
- [ ] OpenAPI schema generation (drf-spectacular)
- [ ] API documentation (`/api/docs/`)
- [ ] Mobile client contract documentation
- [ ] Integration tests for all endpoints

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
