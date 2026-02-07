# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project will follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html) when releases begin.

## [Unreleased]

### Added

#### 2026-02-08 - Phase 2 Foundations Complete
- Created Django project structure with ASGI/Channels/Daphne support
- Implemented settings split by environment (local, test, production)
- Added pydantic-settings for typed environment configuration
- Created `config/` package with settings, ASGI, WSGI, Celery, URLs
- Created `shared/` package with base models, middleware, exceptions
- Implemented correlation ID and tenant context middleware
- Added base models: `BaseModel`, `TenantModel`, `SoftDeleteModel`
- Added custom exception handler with standardized error format
- Implemented structured logging with structlog
- Added health check endpoints (`/health/`, `/health/ready/`)
- Created Celery configuration with Redis broker
- Added custom JWT token serializer with tenant claims
- Created Docker multi-stage build for development and production
- Added docker-compose configuration for local development
- Set up PostgreSQL 16 and Redis 7.2 containers
- Created test suite structure with conftest.py and fixtures
- Created accounts module with custom User model and authentication
- Implemented JWT and session-based authentication
- Added email verification and password reset flows
- Implemented rate limiting on auth endpoints (login, register, password reset)
- Added account lockout after 5 failed login attempts
- Enforced password policy (12+ chars, uppercase, lowercase, digit, special)
- Created demo module with outbox pattern for event dispatch
- Implemented WebSocket consumer for real-time notifications
- Added JWT authentication for WebSocket connections
- Created Celery tasks for outbox processing and notifications

#### 2026-02-07 - Phase 0 Discovery Complete
- Defined user roles and permissions (Anonymous, User, Premium, SuperAdmin)
- Specified tenant context source (JWT claim for API, session for web)
- Selected single-entry accounting model for B2C personal finance
- Defined currency scope with 7 initial currencies (USD, EUR, GBP, CAD, AUD, JPY, INR)
- Established audit log retention policy (7 years financial, 2 years security)
- Defined audit access control per role

#### 2026-02-07 - Baseline Completion
- Added internationalization (i18n) requirements and rules
- Added accessibility (a11y) requirements with WCAG 2.1 AA compliance
- Added domain glossary with core business terms
- Added comprehensive error handling rules and patterns
- Added detailed logging rules with examples
- Added code review rules and SLAs
- Added database migration rules with safe patterns
- Added dependency management rules
- Added performance rules with targets
- Added environment promotion rules
- Added feature flag rules and lifecycle

#### 2026-02-07 - Tech Stack Baseline
- Created `docs/TECH_STACK.md` with complete version matrix for all dependencies
- Created `pyproject.toml` with pinned dependencies and tool configuration
- Created `.pre-commit-config.yaml` for automated code quality checks
- Created `.env.example` with all environment variables documented
- Created `Makefile` with standard development commands
- Created `docs/decision-log/0002-tech-stack-selection.md` ADR documenting technology choices
- Created `docs/decision-log/0003-b2c-saas-requirements.md` ADR for B2C SaaS requirements
- Added B2C SaaS requirements section to ENGINEERING_BASELINE.md
- Expanded `docs/conventions.md` with comprehensive naming and coding standards
- Created `docs/PRODUCT_BASELINE.md` with complete B2C SaaS product strategy
- Consolidated documentation to 7 core baseline files
- Verified accuracy and consistency across all baseline documents

#### 2026-02-07 - Documentation Baseline
- Initial documentation set: README, project plan, engineering baseline, and changelog
- Security and conventions documentation
- ADR process established under `docs/decision-log/`

#### 2026-02-07 - Engineering Standards
- Python 3.12+ with Django 5.2 LTS as runtime baseline
- Django REST Framework 3.16+ for API development
- Django Channels 4.3+ with Daphne for WebSocket support
- Celery 5.6+ for background task processing
- PostgreSQL 16+ as primary database
- Redis 7.2+ for cache and message broker
- Defined async-first rules and Celery usage guidance
- Established Clean/Hexagonal architecture with modular monolith pattern
- Defined multi-tenancy design with single-database tenant scoping
- Established financial data handling rules (Decimal, currency, immutability)
- Defined authentication baseline (sessions for web, JWT for API)
- Established security baseline with encryption, audit logging, and secrets management
- Defined observability requirements (structured logging, correlation IDs, health checks)
- Established testing strategy with 80% coverage target
- Defined CI pipeline with lint, typecheck, security, test, and contract checks
- Established Git workflow with Conventional Commits
- Created AI usage policy requiring adherence to baseline standards

### Changed

#### 2026-02-07 - Documentation Updates
- Enhanced `docs/ENGINEERING_BASELINE.md` with comprehensive rules and regulations
- Updated `README.md` with accurate tech stack and quick start guide
- Enhanced `docs/security.md` with specific configuration examples
- Enhanced `docs/conventions.md` with detailed naming and coding standards

## Post-Production Maintenance

Use this section after the first production release.

### Template
```
### [X.Y.Z] - YYYY-MM-DD
#### Added
- New features

#### Changed
- Changes to existing features

#### Deprecated
- Features to be removed in future

#### Removed
- Removed features

#### Fixed
- Bug fixes

#### Security
- Security patches
```
