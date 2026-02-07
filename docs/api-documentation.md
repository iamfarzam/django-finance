# Django Finance API Documentation

This document provides comprehensive API documentation for the Django Finance platform.

## Base URL

All API endpoints are served under:
```
/api/v1/
```

## Authentication

The API uses JWT (JSON Web Token) for authentication.

### Obtaining Tokens

**Endpoint:** `POST /api/v1/auth/token/`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "your-password"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGci...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGci..."
}
```

### Using Tokens

Include the access token in the `Authorization` header:
```
Authorization: Bearer <access_token>
```

### Refreshing Tokens

**Endpoint:** `POST /api/v1/auth/token/refresh/`

**Request:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGci..."
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGci..."
}
```

### Token Lifetimes

- Access token: 15 minutes (configurable)
- Refresh token: 7 days (configurable)

## Rate Limiting

| Endpoint Type | Anonymous | User | Premium |
|---------------|-----------|------|---------|
| General API | 100/hour | 1000/hour | 1000/hour |
| Finance API | N/A | 200/hour | 1000/hour |
| Transactions | N/A | 100/hour | 500/hour |
| Transfers | N/A | 50/hour | 250/hour |
| Reports | N/A | 30/hour | 100/hour |

## Error Responses

All errors follow a standard format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": [
      {
        "field": "field_name",
        "message": "Field-specific error"
      }
    ],
    "correlation_id": "uuid-for-debugging"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| AUTHENTICATION_FAILED | 401 | Invalid or missing credentials |
| PERMISSION_DENIED | 403 | User lacks required permissions |
| NOT_FOUND | 404 | Resource not found |
| VALIDATION_ERROR | 400 | Request data validation failed |
| THROTTLED | 429 | Rate limit exceeded |
| INTERNAL_ERROR | 500 | Internal server error |

## Pagination

List endpoints use cursor-based pagination:

```json
{
  "next": "/api/v1/transactions/?cursor=cD0yMDIz...",
  "previous": null,
  "results": [...]
}
```

Default page size: 20 items

## Supported Currencies

| Code | Name | Decimal Places |
|------|------|----------------|
| USD | US Dollar | 2 |
| EUR | Euro | 2 |
| GBP | British Pound | 2 |
| CAD | Canadian Dollar | 2 |
| AUD | Australian Dollar | 2 |
| JPY | Japanese Yen | 0 |
| INR | Indian Rupee | 2 |

---

## Endpoints

### Accounts

#### List Accounts
`GET /api/v1/finance/accounts/`

Returns all accounts for the authenticated user's tenant.

**Query Parameters:**
- `search` - Search by account name
- `account_type` - Filter by type (checking, savings, credit_card, investment, cash, other)
- `status` - Filter by status (active, closed, frozen)

**Response:** `200 OK`
```json
{
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "name": "Checking Account",
      "account_type": "checking",
      "currency_code": "USD",
      "status": "active",
      "institution": "Bank Name",
      "account_number_masked": "****1234",
      "is_included_in_net_worth": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### Create Account
`POST /api/v1/finance/accounts/`

**Request:**
```json
{
  "name": "Checking Account",
  "account_type": "checking",
  "currency_code": "USD",
  "institution": "Bank Name",
  "account_number_masked": "****1234",
  "notes": "Primary checking account"
}
```

**Response:** `201 Created`

#### Get Account
`GET /api/v1/finance/accounts/{id}/`

**Response:** `200 OK`

#### Update Account
`PATCH /api/v1/finance/accounts/{id}/`

**Request:**
```json
{
  "name": "New Name",
  "notes": "Updated notes"
}
```

**Response:** `200 OK`

#### Get Account Balance
`GET /api/v1/finance/accounts/{id}/balance/`

**Response:** `200 OK`
```json
{
  "account_id": "uuid",
  "balance": "1000.00",
  "total_credits": "5000.00",
  "total_debits": "4000.00",
  "transaction_count": 50,
  "currency_code": "USD",
  "as_of_date": null
}
```

#### Close Account
`POST /api/v1/finance/accounts/{id}/close/`

**Response:** `200 OK`

#### Reopen Account
`POST /api/v1/finance/accounts/{id}/reopen/`

**Response:** `200 OK`

---

### Transactions

#### List Transactions
`GET /api/v1/finance/transactions/`

**Query Parameters:**
- `account_id` - Filter by account UUID
- `transaction_type` - Filter by type (credit, debit)
- `status` - Filter by status (pending, posted, voided)
- `category` - Filter by category UUID

**Response:** `200 OK`
```json
{
  "results": [
    {
      "id": "uuid",
      "account": "uuid",
      "transaction_type": "credit",
      "amount": "500.00",
      "currency_code": "USD",
      "status": "posted",
      "transaction_date": "2024-01-15",
      "posted_at": "2024-01-15T10:00:00Z",
      "description": "Salary deposit",
      "category": "uuid",
      "category_name": "Income",
      "signed_amount": "500.00",
      "formatted_amount": "+$500.00"
    }
  ]
}
```

#### Create Transaction
`POST /api/v1/finance/transactions/`

**Request:**
```json
{
  "account_id": "uuid",
  "transaction_type": "credit",
  "amount": "500.00",
  "currency_code": "USD",
  "description": "Salary deposit",
  "transaction_date": "2024-01-15",
  "category_id": "uuid",
  "auto_post": true,
  "idempotency_key": "unique-key-123"
}
```

**Response:** `201 Created`

#### Get Transaction
`GET /api/v1/finance/transactions/{id}/`

**Response:** `200 OK`

#### Post Transaction
`POST /api/v1/finance/transactions/{id}/post/`

Posts a pending transaction.

**Response:** `200 OK`

#### Void Transaction
`POST /api/v1/finance/transactions/{id}/void/`

Voids a transaction (cannot be undone).

**Request:**
```json
{
  "reason": "Duplicate entry"
}
```

**Response:** `200 OK`

---

### Transfers

#### List Transfers
`GET /api/v1/finance/transfers/`

**Response:** `200 OK`
```json
{
  "results": [
    {
      "id": "uuid",
      "from_account": "uuid",
      "to_account": "uuid",
      "amount": "500.00",
      "currency_code": "USD",
      "transfer_date": "2024-01-15",
      "description": "Savings transfer",
      "created_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

#### Create Transfer
`POST /api/v1/finance/transfers/`

**Request:**
```json
{
  "from_account_id": "uuid",
  "to_account_id": "uuid",
  "amount": "500.00",
  "currency_code": "USD",
  "transfer_date": "2024-01-15",
  "description": "Monthly savings",
  "idempotency_key": "unique-key-456"
}
```

**Response:** `201 Created`

**Note:** Transfers automatically create two transactions:
- A debit on the source account
- A credit on the destination account

---

### Assets

#### List Assets
`GET /api/v1/finance/assets/`

**Response:** `200 OK`
```json
{
  "results": [
    {
      "id": "uuid",
      "name": "Investment Portfolio",
      "asset_type": "investment",
      "current_value": "50000.00",
      "currency_code": "USD",
      "purchase_date": "2023-01-01",
      "purchase_price": "40000.00",
      "gain_loss": "10000.00",
      "formatted_value": "$50,000.00",
      "is_included_in_net_worth": true
    }
  ]
}
```

#### Create Asset
`POST /api/v1/finance/assets/`

**Request:**
```json
{
  "name": "Investment Portfolio",
  "asset_type": "investment",
  "current_value": "50000.00",
  "currency_code": "USD",
  "purchase_date": "2023-01-01",
  "purchase_price": "40000.00",
  "description": "Stock portfolio"
}
```

**Response:** `201 Created`

#### Update Asset Value
`POST /api/v1/finance/assets/{id}/update-value/`

**Request:**
```json
{
  "new_value": "55000.00"
}
```

**Response:** `200 OK`

---

### Liabilities

#### List Liabilities
`GET /api/v1/finance/liabilities/`

**Response:** `200 OK`
```json
{
  "results": [
    {
      "id": "uuid",
      "name": "Credit Card",
      "liability_type": "credit_card",
      "current_balance": "5000.00",
      "currency_code": "USD",
      "interest_rate": "18.99",
      "minimum_payment": "100.00",
      "due_day": 15
    }
  ]
}
```

#### Create Liability
`POST /api/v1/finance/liabilities/`

**Request:**
```json
{
  "name": "Credit Card",
  "liability_type": "credit_card",
  "current_balance": "5000.00",
  "currency_code": "USD",
  "interest_rate": "18.99",
  "minimum_payment": "100.00",
  "due_day": 15,
  "creditor": "Bank Name"
}
```

**Response:** `201 Created`

---

### Loans

#### List Loans
`GET /api/v1/finance/loans/`

**Response:** `200 OK`
```json
{
  "results": [
    {
      "id": "uuid",
      "name": "Auto Loan",
      "liability_type": "auto_loan",
      "original_principal": "25000.00",
      "current_balance": "20000.00",
      "interest_rate": "5.50",
      "payment_amount": "500.00",
      "payment_frequency": "monthly",
      "status": "active",
      "principal_paid": "5000.00",
      "principal_paid_percentage": "20.00"
    }
  ]
}
```

#### Create Loan
`POST /api/v1/finance/loans/`

**Request:**
```json
{
  "name": "Auto Loan",
  "liability_type": "auto_loan",
  "principal": "25000.00",
  "currency_code": "USD",
  "interest_rate": "5.50",
  "payment_amount": "500.00",
  "payment_frequency": "monthly",
  "start_date": "2024-01-01",
  "lender": "Bank Name"
}
```

**Response:** `201 Created`

#### Record Loan Payment
`POST /api/v1/finance/loans/{id}/record-payment/`

**Request:**
```json
{
  "principal_amount": "450.00",
  "interest_amount": "50.00"
}
```

**Response:** `200 OK`

---

### Categories

#### List Categories
`GET /api/v1/finance/categories/`

**Response:** `200 OK`
```json
{
  "results": [
    {
      "id": "uuid",
      "name": "Groceries",
      "parent": null,
      "icon": "shopping-cart",
      "color": "#4CAF50",
      "is_system": false,
      "is_income": false
    }
  ]
}
```

#### Create Category
`POST /api/v1/finance/categories/`

**Request:**
```json
{
  "name": "Groceries",
  "parent_id": null,
  "icon": "shopping-cart",
  "color": "#4CAF50",
  "is_income": false
}
```

**Response:** `201 Created`

---

### Reports

#### Net Worth
`GET /api/v1/finance/reports/net-worth/`

**Query Parameters:**
- `currency` - Base currency for conversion (default: USD)

**Response:** `200 OK`
```json
{
  "total_assets": "100000.00",
  "total_liabilities": "30000.00",
  "net_worth": "70000.00",
  "account_balances": "25000.00",
  "asset_count": 3,
  "liability_count": 2,
  "account_count": 4,
  "currency_code": "USD",
  "calculated_at": "2024-01-15T10:00:00Z"
}
```

---

## Mobile Client Integration

### Recommended Patterns

1. **Token Storage**: Store JWT tokens securely using platform-specific secure storage (Keychain on iOS, EncryptedSharedPreferences on Android).

2. **Token Refresh**: Implement automatic token refresh when access token expires. Use the refresh token endpoint before the access token expires.

3. **Offline Support**: Cache API responses locally for offline viewing. Use idempotency keys for write operations to prevent duplicates when retrying.

4. **Real-time Updates**: Connect to WebSocket at `/ws/notifications/` for real-time transaction updates.

### WebSocket Connection

```javascript
const socket = new WebSocket('wss://api.example.com/ws/notifications/');

// Include auth token in query params
const socket = new WebSocket('wss://api.example.com/ws/notifications/?token=ACCESS_TOKEN');
```

### Idempotency Keys

For financial write operations, include an `idempotency_key` to prevent duplicate transactions:

```json
{
  "idempotency_key": "unique-client-generated-id",
  // ... other fields
}
```

- Generate a unique key per operation attempt
- The server will return the same response for duplicate keys within 24 hours
- Use UUID v4 or similar for key generation

---

## OpenAPI Schema

Interactive API documentation is available at:

- **Swagger UI**: `/api/docs/`
- **ReDoc**: `/api/redoc/`
- **OpenAPI JSON**: `/api/schema/`

## Changelog

See [CHANGELOG.md](./CHANGELOG.md) for API version history and breaking changes.
