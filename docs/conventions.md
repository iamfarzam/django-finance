# Conventions

This document defines all naming conventions, coding standards, and structural patterns for the project. Consistency is mandatory.

> **Enforcement**: These conventions are enforced via pre-commit hooks, CI checks, and code review.

---

## Table of Contents

1. [General Principles](#general-principles)
2. [File and Directory Naming](#file-and-directory-naming)
3. [Python Coding Standards](#python-coding-standards)
4. [Django Structure](#django-structure)
5. [Model Conventions](#model-conventions)
6. [API Conventions](#api-conventions)
7. [Template Conventions](#template-conventions)
8. [Testing Conventions](#testing-conventions)
9. [Database Conventions](#database-conventions)
10. [Configuration Conventions](#configuration-conventions)
11. [Git Conventions](#git-conventions)
12. [Documentation Conventions](#documentation-conventions)

---

## General Principles

1. **Explicit over implicit**: Names should be self-documenting
2. **Consistent patterns**: Same concept = same naming pattern everywhere
3. **Domain language**: Use business terms from the domain glossary
4. **No abbreviations**: Except universally known ones (id, url, http, api)
5. **American English**: Use American spelling (color, not colour)

---

## File and Directory Naming

### Python Files

| Type | Convention | Example |
|------|------------|---------|
| Module directory | `snake_case` | `user_accounts/` |
| Python file | `snake_case.py` | `use_cases.py` |
| Test file | `test_<name>.py` | `test_use_cases.py` |
| Conftest | `conftest.py` | `conftest.py` |
| Package init | `__init__.py` | `__init__.py` |

### Standard File Names per Layer

```
modules/<module_name>/
├── __init__.py
├── domain/
│   ├── __init__.py
│   ├── entities.py          # Domain entities
│   ├── value_objects.py     # Value objects
│   ├── services.py          # Domain services
│   ├── events.py            # Domain events
│   ├── exceptions.py        # Domain exceptions
│   └── interfaces.py        # Abstract interfaces (if needed)
├── application/
│   ├── __init__.py
│   ├── use_cases.py         # Application use-cases
│   ├── commands.py          # Command handlers
│   ├── queries.py           # Query handlers
│   ├── interfaces.py        # Repository/service interfaces
│   ├── dto.py               # Data transfer objects
│   └── exceptions.py        # Application exceptions
├── infrastructure/
│   ├── __init__.py
│   ├── models.py            # Django ORM models
│   ├── repositories.py      # Repository implementations
│   ├── services.py          # External service implementations
│   ├── tasks.py             # Celery tasks
│   ├── signals.py           # Django signals
│   ├── admin.py             # Admin configuration
│   └── migrations/          # Database migrations
└── interfaces/
    ├── __init__.py
    ├── views.py             # DRF views/viewsets
    ├── serializers.py       # DRF serializers
    ├── filters.py           # DRF filters
    ├── permissions.py       # Custom permissions
    ├── consumers.py         # Channels consumers
    ├── routing.py           # WebSocket routing
    └── urls.py              # URL configuration
```

### Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project configuration, dependencies, tool settings |
| `.env` | Environment variables (never committed) |
| `.env.example` | Environment template (committed) |
| `.pre-commit-config.yaml` | Pre-commit hooks |
| `Makefile` | Development commands |
| `docker-compose.yml` | Docker services |
| `Dockerfile` | Container build |

### Documentation Files

| File | Convention |
|------|------------|
| Main docs | `SCREAMING_CASE.md` (e.g., `README.md`, `CHANGELOG.md`) |
| Reference docs | `kebab-case.md` (e.g., `architecture.md`) |
| ADRs | `NNNN-kebab-case.md` (e.g., `0001-tech-stack.md`) |

---

## Python Coding Standards

### Naming Conventions

#### Classes

| Type | Convention | Example |
|------|------------|---------|
| Domain Entity | `PascalCase` noun | `User`, `Transaction`, `Account` |
| Value Object | `PascalCase` noun | `Money`, `EmailAddress`, `DateRange` |
| Aggregate Root | `PascalCase` noun | `Order`, `Invoice` |
| Domain Service | `PascalCase` + `Service` | `TransferService`, `PricingService` |
| Domain Event | `PascalCase` past tense | `UserCreated`, `PaymentProcessed` |
| Repository Interface | `PascalCase` + `Repository` | `UserRepository`, `OrderRepository` |
| Use Case | `PascalCase` verb phrase | `CreateUser`, `ProcessPayment` |
| Command | `PascalCase` + `Command` | `CreateUserCommand`, `UpdateProfileCommand` |
| Query | `PascalCase` + `Query` | `GetUserQuery`, `ListTransactionsQuery` |
| DTO | `PascalCase` + `DTO` | `UserDTO`, `TransactionDTO` |
| Exception | `PascalCase` + `Error` | `ValidationError`, `NotFoundError` |
| Django Model | `PascalCase` (no suffix) | `User`, `Transaction` |
| Serializer | `PascalCase` + `Serializer` | `UserSerializer`, `TransactionSerializer` |
| ViewSet | `PascalCase` + `ViewSet` | `UserViewSet`, `TransactionViewSet` |
| View | `PascalCase` + `View` | `UserDetailView`, `LoginView` |
| Filter | `PascalCase` + `Filter` | `TransactionFilter`, `UserFilter` |
| Permission | `PascalCase` | `IsOwner`, `IsAdminUser` |
| Mixin | `PascalCase` + `Mixin` | `TenantMixin`, `AuditMixin` |
| Abstract Base | `Base` + `PascalCase` | `BaseModel`, `BaseService` |
| Factory | `PascalCase` + `Factory` | `UserFactory`, `TransactionFactory` |

#### Functions and Methods

| Type | Convention | Example |
|------|------------|---------|
| Public function | `snake_case` verb | `create_user()`, `calculate_total()` |
| Public method | `snake_case` verb | `process_payment()`, `validate_input()` |
| Private function | `_snake_case` | `_calculate_tax()`, `_validate_email()` |
| Private method | `_snake_case` | `_get_cached_value()` |
| Property | `snake_case` noun | `@property def total_amount` |
| Classmethod | `snake_case` | `@classmethod def from_dict()` |
| Staticmethod | `snake_case` | `@staticmethod def generate_id()` |
| Async function | `snake_case` (no prefix) | `async def fetch_user()` |
| Test function | `test_<description>` | `test_creates_user_successfully()` |

#### Variables

| Type | Convention | Example |
|------|------------|---------|
| Local variable | `snake_case` | `user_count`, `total_amount` |
| Instance attribute | `snake_case` | `self.created_at`, `self.user_id` |
| Class attribute | `snake_case` | `default_currency = "USD"` |
| Constant | `SCREAMING_SNAKE_CASE` | `MAX_RETRIES`, `DEFAULT_PAGE_SIZE` |
| Private variable | `_snake_case` | `_cache`, `_connection` |
| Module constant | `SCREAMING_SNAKE_CASE` | `API_VERSION`, `BASE_URL` |
| Type variable | `PascalCase` or `_T` | `T`, `UserType`, `_T` |

#### Boolean Variables

Boolean variables and parameters should read as questions:

```python
# Good
is_active = True
has_permission = False
can_edit = True
should_notify = False
was_processed = True

# Bad
active = True
permission = False
edit = True
```

### Import Organization

Imports are organized in this order (enforced by Ruff):

```python
# 1. Future imports
from __future__ import annotations

# 2. Standard library
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

# 3. Django imports
from django.db import models
from django.conf import settings

# 4. Third-party imports
from rest_framework import serializers
from celery import shared_task

# 5. First-party imports (project modules)
from modules.accounts.domain.entities import User
from modules.finance.application.use_cases import CreateTransaction

# 6. Local imports (same package)
from .models import TransactionModel
from .serializers import TransactionSerializer

# 7. Type checking only imports
if TYPE_CHECKING:
    from modules.accounts.domain.entities import Account
```

### Type Hints

```python
from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from collections.abc import Sequence

# Use built-in generics (Python 3.12+)
def process_items(items: list[str]) -> dict[str, int]:
    ...

# Use union syntax
def find_user(user_id: UUID) -> User | None:
    ...

# Type aliases for complex types
TransactionList = list[Transaction]
UserMapping = dict[UUID, User]

# Callable types
from collections.abc import Callable
Handler = Callable[[Request], Response]
```

### Docstrings (Google Style)

```python
def transfer_funds(
    from_account: Account,
    to_account: Account,
    amount: Money,
    description: str = "",
) -> Transaction:
    """Transfer funds between two accounts.

    Validates sufficient balance, creates transaction records for both
    accounts, and emits TransferCompleted event.

    Args:
        from_account: The source account to debit.
        to_account: The destination account to credit.
        amount: The amount to transfer (must be positive).
        description: Optional description for the transaction.

    Returns:
        The created transaction record.

    Raises:
        InsufficientFundsError: If from_account has insufficient balance.
        InvalidAmountError: If amount is not positive.
        SameAccountError: If from_account equals to_account.

    Example:
        >>> transaction = transfer_funds(
        ...     from_account=savings,
        ...     to_account=checking,
        ...     amount=Money(100, "USD"),
        ... )
    """
```

### Class Structure

```python
class TransactionService:
    """Service for managing financial transactions.

    Handles creation, validation, and processing of transactions
    with full audit logging and tenant isolation.
    """

    # Class constants
    MAX_AMOUNT = Decimal("999999999.9999")
    DEFAULT_CURRENCY = "USD"

    # Class variables (shared state - use sparingly)
    _cache: dict[UUID, Transaction] = {}

    def __init__(
        self,
        repository: TransactionRepository,
        event_publisher: EventPublisher,
    ) -> None:
        """Initialize the service.

        Args:
            repository: Transaction persistence layer.
            event_publisher: Event publishing interface.
        """
        self._repository = repository
        self._event_publisher = event_publisher

    # Properties first
    @property
    def supported_currencies(self) -> list[str]:
        """List of supported currency codes."""
        return ["USD", "EUR", "GBP"]

    # Public methods
    def create_transaction(self, command: CreateTransactionCommand) -> Transaction:
        """Create a new transaction."""
        ...

    def get_transaction(self, transaction_id: UUID) -> Transaction | None:
        """Retrieve a transaction by ID."""
        ...

    # Private methods last
    def _validate_amount(self, amount: Decimal) -> None:
        """Validate transaction amount."""
        ...
```

---

## Django Structure

### Project Layout

```
django-finance/
├── config/                      # Project configuration
│   ├── __init__.py
│   ├── asgi.py                 # ASGI application
│   ├── wsgi.py                 # WSGI application (fallback)
│   ├── urls.py                 # Root URL configuration
│   ├── celery.py               # Celery configuration
│   └── settings/
│       ├── __init__.py
│       ├── base.py             # Base settings
│       ├── local.py            # Local development
│       ├── test.py             # Test environment
│       └── production.py       # Production settings
├── modules/                     # Feature modules
│   ├── __init__.py
│   ├── accounts/
│   ├── finance/
│   └── notifications/
├── shared/                      # Shared utilities
│   ├── __init__.py
│   ├── models.py               # Base models (TenantModel, etc.)
│   ├── middleware.py           # Custom middleware
│   ├── exceptions.py           # Base exceptions
│   └── utils.py                # Utility functions
├── contracts/                   # API/event contracts
├── tests/                       # Test suite
├── templates/                   # Django templates
├── static/                      # Static files
└── manage.py
```

### App Registration

```python
# config/settings/base.py
INSTALLED_APPS = [
    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "rest_framework",
    "drf_spectacular",
    "channels",
    "django_celery_beat",
    "django_filters",
    "corsheaders",

    # Project modules
    "modules.accounts.infrastructure",
    "modules.finance.infrastructure",
    "modules.notifications.infrastructure",

    # Shared
    "shared",
]
```

---

## Model Conventions

### Model Naming

| Type | Convention | Example |
|------|------------|---------|
| Model class | `PascalCase` singular noun | `User`, `Transaction`, `Account` |
| Abstract model | `Base` prefix or `Abstract` prefix | `BaseModel`, `AbstractTenant` |
| Through model | `<Model1><Model2>` | `UserRole`, `AccountPermission` |
| Proxy model | Same as parent or descriptive | `ActiveUser`, `ArchivedTransaction` |

### Field Naming

| Field Type | Convention | Example |
|------------|------------|---------|
| Primary key | `id` (UUID) | `id = models.UUIDField(primary_key=True)` |
| Foreign key | `<related_model>` (singular) | `account`, `user`, `category` |
| Foreign key ID | `<related_model>_id` (auto) | `account_id`, `user_id` |
| Many-to-many | `<related_model>s` (plural) | `tags`, `permissions`, `categories` |
| Boolean | `is_`, `has_`, `can_`, `should_` | `is_active`, `has_verified`, `can_edit` |
| DateTime | `<action>_at` | `created_at`, `updated_at`, `deleted_at` |
| Date | `<action>_date` or `<noun>_date` | `birth_date`, `due_date` |
| Count | `<noun>_count` | `login_count`, `view_count` |
| Amount/Money | `<noun>_amount` or `<noun>` | `amount`, `balance`, `total_amount` |
| Status | `status` or `<noun>_status` | `status`, `payment_status` |
| Type | `type` or `<noun>_type` | `type`, `transaction_type` |
| JSON | `<noun>_data` or `metadata` | `settings_data`, `metadata` |
| File | `<noun>_file` or `<noun>` | `avatar`, `document_file` |
| URL | `<noun>_url` | `website_url`, `callback_url` |

### Standard Fields

```python
import uuid
from django.db import models


class BaseModel(models.Model):
    """Abstract base model with standard fields."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TenantModel(BaseModel):
    """Abstract model with tenant isolation."""

    tenant_id = models.UUIDField(db_index=True)

    class Meta:
        abstract = True


class SoftDeleteModel(BaseModel):
    """Abstract model with soft delete support."""

    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True
```

### Complete Model Example

```python
import uuid
from decimal import Decimal

from django.db import models
from django.core.validators import MinValueValidator

from shared.models import TenantModel


class Transaction(TenantModel):
    """Financial transaction record.

    Represents a single financial transaction (credit or debit)
    against an account. Transactions are immutable once created.
    """

    class TransactionType(models.TextChoices):
        """Transaction type choices."""

        CREDIT = "credit", "Credit"
        DEBIT = "debit", "Debit"
        TRANSFER = "transfer", "Transfer"
        ADJUSTMENT = "adjustment", "Adjustment"

    class TransactionStatus(models.TextChoices):
        """Transaction status choices."""

        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        REVERSED = "reversed", "Reversed"

    # Relationships
    account = models.ForeignKey(
        "accounts.Account",
        on_delete=models.PROTECT,
        related_name="transactions",
        help_text="The account this transaction belongs to.",
    )
    category = models.ForeignKey(
        "finance.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
        help_text="Optional category for the transaction.",
    )

    # Transaction details
    amount = models.DecimalField(
        max_digits=19,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0.0001"))],
        help_text="Transaction amount (always positive).",
    )
    currency = models.CharField(
        max_length=3,
        help_text="ISO 4217 currency code.",
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
        db_index=True,
        help_text="Type of transaction.",
    )
    status = models.CharField(
        max_length=20,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING,
        db_index=True,
        help_text="Current status of the transaction.",
    )

    # Metadata
    description = models.TextField(
        blank=True,
        help_text="User-provided description.",
    )
    reference = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        help_text="External reference number.",
    )
    idempotency_key = models.CharField(
        max_length=64,
        unique=True,
        help_text="Unique key for idempotent requests.",
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata as JSON.",
    )

    # Timestamps
    transaction_date = models.DateField(
        db_index=True,
        help_text="The date of the transaction.",
    )
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the transaction was processed.",
    )

    class Meta:
        db_table = "finance_transactions"
        ordering = ["-created_at"]
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        indexes = [
            models.Index(
                fields=["tenant_id", "account", "created_at"],
                name="idx_txn_tenant_account_created",
            ),
            models.Index(
                fields=["tenant_id", "transaction_date"],
                name="idx_txn_tenant_date",
            ),
            models.Index(
                fields=["tenant_id", "status"],
                name="idx_txn_tenant_status",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount__gt=0),
                name="chk_transaction_positive_amount",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.transaction_type} {self.amount} {self.currency}"

    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, type={self.transaction_type}, amount={self.amount})>"
```

### Relationship Naming

| Relationship | Field Name | Related Name |
|--------------|------------|--------------|
| ForeignKey | Singular noun | Plural noun |
| OneToOne | Singular noun | Singular noun |
| ManyToMany | Plural noun | Plural noun |

```python
# ForeignKey
account = models.ForeignKey(
    "Account",
    related_name="transactions",  # account.transactions.all()
)

# OneToOne
profile = models.OneToOneField(
    "Profile",
    related_name="user",  # profile.user
)

# ManyToMany
tags = models.ManyToManyField(
    "Tag",
    related_name="transactions",  # tag.transactions.all()
)
```

---

## API Conventions

### URL Patterns

| Pattern | Convention | Example |
|---------|------------|---------|
| Collection | `/api/v1/<resource>/` | `/api/v1/transactions/` |
| Item | `/api/v1/<resource>/<id>/` | `/api/v1/transactions/{id}/` |
| Nested | `/api/v1/<parent>/<id>/<child>/` | `/api/v1/accounts/{id}/transactions/` |
| Action | `/api/v1/<resource>/<id>/<action>/` | `/api/v1/transactions/{id}/reverse/` |
| Search | `/api/v1/<resource>/search/` | `/api/v1/transactions/search/` |

### URL Naming

```python
# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("transactions", TransactionViewSet, basename="transaction")
router.register("accounts", AccountViewSet, basename="account")

urlpatterns = [
    path("api/v1/", include(router.urls)),
]

# URL names follow pattern: <basename>-list, <basename>-detail
# transaction-list, transaction-detail
# account-list, account-detail
```

### Query Parameters

| Type | Convention | Example |
|------|------------|---------|
| Filter | `snake_case` | `?status=completed&account_id=...` |
| Search | `search` | `?search=groceries` |
| Ordering | `ordering` | `?ordering=-created_at` |
| Pagination | `cursor`, `limit` | `?cursor=...&limit=20` |
| Date range | `<field>_after`, `<field>_before` | `?created_after=2024-01-01` |
| Include | `include` | `?include=account,category` |
| Fields | `fields` | `?fields=id,amount,status` |

### Response Format

```python
# Success response
{
    "data": { ... },
    "meta": {
        "pagination": {
            "cursor": "eyJpZCI6...",
            "has_next": true,
            "has_previous": false
        }
    }
}

# Error response
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Validation failed",
        "details": [
            {
                "field": "amount",
                "code": "invalid",
                "message": "Amount must be positive"
            }
        ]
    }
}
```

### Serializer Naming

| Type | Convention | Example |
|------|------------|---------|
| Read serializer | `<Model>Serializer` | `TransactionSerializer` |
| Create serializer | `<Model>CreateSerializer` | `TransactionCreateSerializer` |
| Update serializer | `<Model>UpdateSerializer` | `TransactionUpdateSerializer` |
| List serializer | `<Model>ListSerializer` | `TransactionListSerializer` |
| Detail serializer | `<Model>DetailSerializer` | `TransactionDetailSerializer` |
| Nested serializer | `<Model>NestedSerializer` | `AccountNestedSerializer` |

---

## Template Conventions

### Template File Naming

```
templates/
├── base.html                           # Site-wide base
├── components/                         # Reusable components
│   ├── _button.html                   # Partial (underscore prefix)
│   ├── _card.html
│   └── _pagination.html
├── layouts/                            # Page layouts
│   ├── default.html
│   └── dashboard.html
├── <app_name>/                         # App-specific templates
│   ├── <model>_list.html              # List view
│   ├── <model>_detail.html            # Detail view
│   ├── <model>_form.html              # Create/Update form
│   ├── <model>_confirm_delete.html    # Delete confirmation
│   └── partials/                       # HTMX partials
│       └── _<model>_row.html
└── emails/                             # Email templates
    ├── base.html
    └── <action>.html                   # e.g., welcome.html
```

### Template Naming Examples

| View Type | Template Name |
|-----------|---------------|
| List | `transaction_list.html` |
| Detail | `transaction_detail.html` |
| Create | `transaction_form.html` |
| Update | `transaction_form.html` (shared) |
| Delete | `transaction_confirm_delete.html` |
| Partial | `_transaction_row.html` |

---

## Testing Conventions

### Test File Organization

```
tests/
├── conftest.py                  # Shared fixtures
├── factories.py                 # Factory definitions
├── unit/
│   └── modules/
│       └── <module>/
│           ├── domain/
│           │   └── test_entities.py
│           └── application/
│               └── test_use_cases.py
├── integration/
│   ├── api/
│   │   └── test_<resource>.py
│   └── channels/
│       └── test_consumers.py
└── e2e/
    └── test_<user_journey>.py
```

### Test Naming

```python
class TestTransactionCreation:
    """Tests for transaction creation use case."""

    def test_creates_transaction_with_valid_data(self):
        """Transaction is created when all required fields are valid."""
        ...

    def test_raises_error_when_amount_is_negative(self):
        """InvalidAmountError is raised for negative amounts."""
        ...

    def test_raises_error_when_account_not_found(self):
        """AccountNotFoundError is raised for non-existent account."""
        ...

    def test_emits_transaction_created_event(self):
        """TransactionCreated event is published on success."""
        ...
```

### Factory Naming

```python
class TransactionFactory(factory.django.DjangoModelFactory):
    """Factory for Transaction model."""

    class Meta:
        model = Transaction

    tenant_id = factory.LazyFunction(uuid.uuid4)
    account = factory.SubFactory(AccountFactory)
    amount = factory.Faker("pydecimal", left_digits=5, right_digits=2, positive=True)
    currency = "USD"
    transaction_type = Transaction.TransactionType.CREDIT
```

---

## Database Conventions

### Table Naming

| Type | Convention | Example |
|------|------------|---------|
| Regular table | `<app>_<model>` | `finance_transactions` |
| Join table | `<app>_<model1>_<model2>` | `finance_transaction_tags` |
| Audit table | `<app>_<model>_audit` | `finance_transactions_audit` |

### Index Naming

```python
# Convention: idx_<table>_<columns>
models.Index(
    fields=["tenant_id", "created_at"],
    name="idx_txn_tenant_created",
)
```

### Constraint Naming

```python
# Convention: chk_<table>_<description> or uq_<table>_<columns>
models.CheckConstraint(
    check=models.Q(amount__gt=0),
    name="chk_transaction_positive_amount",
)
models.UniqueConstraint(
    fields=["tenant_id", "reference"],
    name="uq_transaction_tenant_reference",
)
```

---

## Configuration Conventions

### Environment Variables

| Type | Convention | Example |
|------|------------|---------|
| Feature flag | `FEATURE_<NAME>` | `FEATURE_MFA_ENABLED` |
| Service URL | `<SERVICE>_URL` | `DATABASE_URL`, `REDIS_URL` |
| API key | `<SERVICE>_API_KEY` | `STRIPE_API_KEY` |
| Secret | `<NAME>_SECRET` or `SECRET_<NAME>` | `JWT_SECRET_KEY` |
| Timeout | `<SERVICE>_TIMEOUT` | `HTTP_TIMEOUT` |
| Boolean | `<NAME>` (true/false) | `DEBUG`, `FEATURE_MFA_ENABLED` |

### Settings Variables

```python
# Use SCREAMING_SNAKE_CASE for settings
DEBUG = env.bool("DEBUG", default=False)
SECRET_KEY = env.str("SECRET_KEY")
DATABASE_URL = env.str("DATABASE_URL")

# Group related settings with comments
# JWT Settings
JWT_SECRET_KEY = env.str("JWT_SECRET_KEY")
JWT_ACCESS_LIFETIME_MINUTES = env.int("JWT_ACCESS_LIFETIME_MINUTES", default=15)
JWT_REFRESH_LIFETIME_DAYS = env.int("JWT_REFRESH_LIFETIME_DAYS", default=7)
```

### Celery Task Naming

```python
# Convention: <module>.<action>_<noun>
@shared_task(name="notifications.send_email")
def send_email(user_id: str, template: str) -> None:
    ...

@shared_task(name="finance.process_transaction")
def process_transaction(transaction_id: str) -> None:
    ...

@shared_task(name="reports.generate_monthly_report")
def generate_monthly_report(tenant_id: str, month: str) -> None:
    ...
```

### Event Naming

```python
# Convention: <domain>.<entity>.<action> (past tense)
"accounts.user.created"
"accounts.user.email_verified"
"finance.transaction.created"
"finance.transaction.reversed"
"notifications.email.sent"
"notifications.email.failed"
```

---

## Git Conventions

### Branch Naming

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feat/<description>` | `feat/user-authentication` |
| Bug fix | `fix/<description>` | `fix/transaction-rounding` |
| Hotfix | `hotfix/<description>` | `hotfix/security-patch` |
| Refactor | `refactor/<description>` | `refactor/payment-service` |
| Docs | `docs/<description>` | `docs/api-documentation` |
| Chore | `chore/<description>` | `chore/update-dependencies` |

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`

**Examples**:

```
feat(accounts): add email verification flow

Implement email verification for new user registrations.
- Send verification email on signup
- Add verification endpoint
- Expire tokens after 24 hours

Closes #123
```

```
fix(finance): correct decimal rounding for JPY

Japanese Yen has 0 decimal places. Updated rounding
logic to respect currency-specific precision.

Fixes #456
```

---

## Documentation Conventions

### Code Comments

```python
# Explain WHY, not WHAT
# ✓ Track retry attempts for exponential backoff
retry_count += 1

# ✗ Increment retry count
retry_count += 1
```

### Module Docstrings

```python
"""Transaction domain entities.

This module contains the core domain entities for financial transactions,
including Transaction, TransactionType, and related value objects.

Domain Rules:
    - Transactions are immutable once created
    - Amounts are always positive; type indicates credit/debit
    - All transactions require an idempotency key
"""
```

### README in Modules

Each module should have a README.md:

```markdown
# Finance Module

Core financial domain for managing accounts, transactions, and balances.

## Entities
- Transaction: Financial transaction record
- Account: User financial account
- Category: Transaction categorization

## Use Cases
- CreateTransaction: Create a new transaction
- GetBalance: Calculate account balance
- TransferFunds: Transfer between accounts

## Events
- TransactionCreated
- BalanceUpdated

## Dependencies
- accounts: User account reference
```

---

## Quick Reference Card

### Naming At-a-Glance

| Thing | Convention | Example |
|-------|------------|---------|
| Python file | `snake_case.py` | `use_cases.py` |
| Class | `PascalCase` | `TransactionService` |
| Function | `snake_case` | `create_transaction` |
| Variable | `snake_case` | `total_amount` |
| Constant | `SCREAMING_SNAKE_CASE` | `MAX_RETRIES` |
| Model | `PascalCase` | `Transaction` |
| Model field | `snake_case` | `created_at` |
| FK field | singular noun | `account` |
| M2M field | plural noun | `tags` |
| Boolean field | `is_`, `has_`, `can_` | `is_active` |
| DateTime field | `<action>_at` | `created_at` |
| URL path | kebab-case, plural | `/api/v1/transactions/` |
| Template | `snake_case.html` | `transaction_list.html` |
| Partial template | `_snake_case.html` | `_transaction_row.html` |
| Test class | `Test<Subject>` | `TestTransactionCreation` |
| Test method | `test_<description>` | `test_creates_transaction` |
| Branch | `<type>/<description>` | `feat/user-auth` |
| Env var | `SCREAMING_SNAKE_CASE` | `DATABASE_URL` |
| Celery task | `<module>.<action>_<noun>` | `finance.process_transaction` |
| Event | `<domain>.<entity>.<action>` | `finance.transaction.created` |
