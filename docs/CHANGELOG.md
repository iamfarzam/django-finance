# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project will follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html) when releases begin.

## [Unreleased]

### Added

#### 2026-02-08 - Test Suite and Serializer Fixes
- Fixed DRF serializers to implement `create()` methods correctly:
  - All Create*Serializers now properly create model instances
  - ViewSets return read serializers after create operations
- Fixed CategorySerializer to return parent UUID as string
- Added default ordering (`-created_at`) to TenantScopedViewSet for CursorPagination
- Fixed integration tests:
  - Added `transaction_date` to all Transaction.objects.create() calls
  - Corrected URL name for reports API (`report-net-worth`)
  - Updated error response assertions to match custom exception handler format
- Fixed social entity tests to use correct method signatures:
  - `update()` instead of `update_name()`
  - `restore()` instead of `activate()`
  - `record_settlement()` instead of `settle()`
  - Factory methods: `create_lent()`, `create_borrowed()`, `create_owner_pays()`, `create_owner_receives()`
- All 197 tests now pass

#### 2026-02-08 - Phase 8 Admin Modernization Complete
- Created custom admin site with branding in `shared/admin/`:
  - `FinanceAdminSite`: Custom admin with finance-themed styling
  - Dashboard statistics view with financial summaries
  - Audit log visibility page
- Implemented base admin classes and mixins:
  - `TenantScopedAdmin`: Base class with automatic tenant filtering
  - `AuditLogMixin`: Automatic audit logging for admin actions
  - `ExportMixin`: CSV export action for all models
  - `ReadOnlyAdminMixin`: For read-only admin views
  - `SoftDeleteMixin`: For soft delete/restore actions
- Enhanced Accounts admin:
  - Role and status badges with color coding
  - Email verification status display
  - Lock status with visual indicators
  - Actions: Activate, suspend, verify emails, unlock, premium upgrade/revoke
  - Token cleanup actions for expired verification/reset tokens
- Enhanced Finance admin:
  - Transaction inline on accounts for recent activity
  - Status badges (active/closed, pending/posted/voided)
  - Amount displays with color coding (green for credits, red for debits)
  - Progress bars for loan repayment visualization
  - Actions: Activate/close accounts, post/void transactions, include/exclude net worth
  - Gain/loss display for assets
- Enhanced Social admin:
  - Debt inline on contacts for quick balance view
  - Direction badges (lent/borrowed with arrows)
  - Remaining amount highlighting
  - Overdue date warnings for pending debts
  - Settlement display with from→to arrows
  - Payment method badges with colors
  - Actions: Settle debts, mark partial payment, activate/deactivate contacts
- Created custom admin templates:
  - `admin/finance_index.html`: Custom dashboard with quick stats and links
  - `admin/dashboard_stats.html`: Detailed financial statistics page
  - `admin/audit_logs.html`: Audit log information and access guide
- Created admin documentation at `docs/admin.md`:
  - Feature overview and access levels
  - Module-specific admin documentation
  - Bulk actions reference
  - Audit logging guide
  - Security best practices
  - Customization examples

#### 2026-02-08 - Phase 7 Web UI Complete
- Created base template system with TailwindCSS and Alpine.js:
  - `base.html`: Root template with full SEO meta tags, accessibility features
  - `app.html`: Authenticated layout with responsive navigation
  - `auth.html`: Split-screen layout for login/register pages
- Implemented authentication pages:
  - Login page with remember me and error handling
  - Registration page with password validation
  - Password reset request page
  - Profile and settings pages
- Created main dashboard with:
  - Net worth summary (assets, liabilities, net worth)
  - Account stats with quick links
  - Recent transactions list
  - Social finance overview (who owes whom)
- Implemented Personal Finance UI:
  - Accounts list with balance display
  - Account create/update forms
  - Transactions list with filtering
  - Transaction create form
  - Net worth details page
- Implemented Social Finance UI:
  - Contacts list page
  - Contact create/update views
  - Peer debts list/create views
  - Expense groups list/create views
  - Settlements list/create views
  - Balance summary page
- Added SEO components:
  - Dynamic meta tags (title, description, keywords)
  - Open Graph tags for social sharing
  - Twitter Card meta tags
  - robots.txt with sitemap reference
  - XML sitemap using django.contrib.sitemaps
- Implemented accessibility (WCAG 2.1 AA):
  - Skip to main content link
  - Focus visible styles
  - ARIA labels and roles
  - Reduced motion media query
- Created `modules/web/` module with views, URLs, and SEO utilities
- Created web authentication views separate from API views

#### 2026-02-08 - Phase 6 Real-time Features Complete
- Created WebSocket consumers with JWT authentication:
  - `AuthenticatedConsumer`: Base consumer with JWT auth from query string
  - `FinanceConsumer`: Real-time finance updates (balance, transactions, net worth)
  - `SocialConsumer`: Real-time social updates (peer debts, expenses, settlements)
- Implemented notification service in `shared/notifications/`:
  - `NotificationType` enum with 20+ notification types
  - `NotificationChannel` enum for channel layer groups
  - `NotificationPayload` dataclass for message structure
  - `NotificationService` for sending updates to users/groups
- Created connection health monitoring in `shared/consumers/health.py`:
  - `ConnectionState`: Track connection metrics (messages, bytes, latency)
  - `HealthMonitor`: Ping/pong heartbeat with configurable intervals
  - `BackpressureHandler`: Queue-based message sending with priority support
- Implemented event handlers in `shared/events/`:
  - `FinanceEventHandler`: Converts finance domain events to notifications
  - `SocialEventHandler`: Converts social domain events to notifications
- Updated WebSocket routing to include new consumers:
  - `/ws/finance/` - Finance domain real-time updates
  - `/ws/social/` - Social finance real-time updates
- Created integration tests for WebSocket functionality:
  - Health monitoring tests
  - Backpressure handling tests
  - Consumer message handler tests
  - Notification service tests

#### 2026-02-08 - Phase 5 Social Finance Domain Complete
- Created social finance module with clean/hexagonal architecture
- Implemented domain entities:
  - `Contact`: Friends/people with optional user linking, archival support
  - `ContactGroup`: Organize contacts into groups
  - `PeerDebt`: Track money lent/borrowed with partial settlement support
  - `ExpenseGroup`: Container for group expense splitting
  - `GroupExpense`: Shared expenses with automatic equal or exact splits
  - `ExpenseSplit`: Individual share per participant
  - `Settlement`: Record payments between owner and contacts
- Created domain services:
  - `DebtCalculator`: Calculate net balance with a contact
  - `GroupBalanceCalculator`: Calculate who owes whom in a group
  - `SimplifyDebtsService`: Minimize transactions to settle all debts
  - `SettlementSuggestionService`: Suggest optimal settlements
- Implemented domain events for all social finance entities
- Created Django ORM models with tenant scoping and proper indexes
- Implemented repository pattern with Django ORM implementations
- Created DRF serializers for all entities and commands
- Implemented API viewsets:
  - Contacts CRUD with archive support
  - Contact groups CRUD with member management
  - Peer debts CRUD with settle/cancel actions
  - Expense groups CRUD with member management
  - Group expenses CRUD with automatic splitting
  - Settlements CRUD
  - Balance calculations with settlement suggestions
- Added API endpoints at `/api/v1/social/`:
  - `/contacts/` - Contact management
  - `/contact-groups/` - Contact group management
  - `/peer-debts/` - Peer debt tracking with settle/cancel actions
  - `/expense-groups/` - Expense group management
  - `/group-expenses/` - Group expense with auto-splitting
  - `/settlements/` - Settlement recording
  - `/balances/` - Balance calculations and suggestions
- Created comprehensive unit tests for domain logic:
  - Entity tests (contact, debt, expense, settlement)
  - Service tests (balance calculation, debt simplification)
- Added OpenAPI tags for all social finance endpoints
- Integrated social module into INSTALLED_APPS and API URLs

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
