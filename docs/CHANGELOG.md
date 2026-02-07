# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project will follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html) when releases begin.

## [Unreleased]

### Added

#### 2026-02-08 - Project Scope Expansion: Hybrid Finance Platform
- Updated project vision to include social finance features
- Added new scope items:
  - Peer Debts (Udhaar/IOUs): Track money lent/borrowed between contacts
  - Group Expenses: Split shared expenses (Splitwise-like)
  - Contacts: Manage friends/people for social finance
  - Settlements: Record and track debt settlements
- Added Phase 5: Social Finance Domain with detailed deliverables
- Renumbered subsequent phases (Real-time → Phase 6, Web UI → Phase 7, etc.)
- Key decisions for social finance:
  - Contacts can be independent or linked to registered users
  - Same currency per debt/expense (multi-currency planned for future)
  - Privacy: Shared records require explicit invitation
  - Split methods: Equal and exact amounts (Phase 5), percentage/shares (future)

#### 2026-02-08 - Phase 4 API and Integrations Complete
- Created role-based permission classes in `shared/permissions.py`:
  - `IsActiveUser`: Requires active status and verified email
  - `IsPremiumUser`: Premium subscription check
  - `IsSuperAdmin`: Superadmin role check
  - `IsOwner`, `IsOwnerOrReadOnly`: Object-level ownership
  - `TenantIsolation`: Cross-tenant access prevention
  - `CanCreateAccount`: Account limit enforcement (3 for basic users)
- Implemented audit logging system in `shared/audit.py`:
  - `AuditAction` enum with 30+ auditable actions
  - `AuditCategory` for retention classification (financial: 7y, security: 2y)
  - `AuditEvent` dataclass with correlation and context tracking
  - `AuditLogger` singleton for structured audit logging
  - Sensitive field masking for security
- Added `AuditLoggingMiddleware` for automatic API audit logging
- Created finance-specific throttle classes in `modules/finance/interfaces/throttling.py`:
  - `FinanceUserRateThrottle`: 200/hour for regular users
  - `TransactionRateThrottle`: 100/hour for transaction creation
  - `TransferRateThrottle`: 50/hour for transfers
  - `AccountCreationRateThrottle`: 10/hour for account creation
  - `ReportGenerationRateThrottle`: 30/hour for reports
  - `PremiumFinanceRateThrottle`: 1000/hour for premium users
- Enhanced drf-spectacular OpenAPI configuration:
  - Comprehensive API description with authentication guide
  - JWT Bearer security scheme
  - Organized endpoint tags
  - Swagger UI and ReDoc customization
- Added OpenAPI decorators to all finance viewsets with proper tagging
- Created comprehensive API documentation at `docs/api-documentation.md`:
  - Authentication flow documentation
  - Rate limiting documentation
  - All endpoint documentation with examples
  - Mobile client integration guide
  - WebSocket connection guide
  - Idempotency key usage
- Created integration tests in `tests/integration/test_finance_api.py`:
  - Account API tests (CRUD, balance, close/reopen, tenant isolation)
  - Transaction API tests (CRUD, post, void, filtering)
  - Transfer API tests with validation
  - Asset, Liability, Loan API tests
  - Reports API tests (net worth calculation)
  - Category API tests
- Added test fixtures to `tests/conftest.py`:
  - User fixtures (standard, premium, superadmin)
  - Authenticated client fixtures
  - Finance model fixtures (account, category, transaction)

#### 2026-02-08 - Phase 3 Core Domain Modeling Complete
- Created finance module with clean/hexagonal architecture
- Implemented domain entities: Account, Transaction, Transfer, Asset, Liability, Loan, Category
- Created value objects: Money, Currency, IdempotencyKey, ExchangeRate
- Implemented domain services: BalanceCalculator, NetWorthCalculator, CashFlowAnalyzer, TransactionValidator
- Added domain events for all entities (AccountCreated, TransactionPosted, etc.)
- Implemented single-entry accounting model (balance = credits - debits)
- Added monetary precision with Decimal and per-currency decimal places
- Implemented ROUND_HALF_UP rounding policy for financial calculations
- Added immutable transaction support with adjustment workflow
- Implemented idempotency key support for financial writes
- Created tenant-scoped Django ORM models with proper indexes and constraints
- Added Django admin configuration for all finance models
- Created DRF serializers with currency validation
- Implemented API viewsets for accounts, transactions, transfers, assets, liabilities, loans
- Added net worth calculation endpoint
- Created comprehensive unit tests for domain logic (value objects, entities, services)
- Supported currencies: USD, EUR, GBP, CAD, AUD, JPY, INR

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
