# Security Baseline

> **Reference**: See [`ENGINEERING_BASELINE.md`](ENGINEERING_BASELINE.md) for complete security standards.

## Authentication

### Web UI (Session-based)
- Django's built-in authentication system
- Session stored server-side (database or Redis)
- CSRF protection enabled on all forms
- Session cookie settings:
  - `SESSION_COOKIE_SECURE = True` (HTTPS only)
  - `SESSION_COOKIE_HTTPONLY = True` (no JS access)
  - `SESSION_COOKIE_SAMESITE = "Lax"` (CSRF protection)
  - `SESSION_COOKIE_AGE = 1209600` (2 weeks)

### API/Mobile (JWT-based)
- Library: `djangorestframework-simplejwt`
- Access token lifetime: 15 minutes
- Refresh token lifetime: 7 days
- Refresh token rotation: Enabled
- Blacklist: Enabled (for logout/revocation)

```python
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "AUTH_HEADER_TYPES": ("Bearer",),
}
```

### WebSocket
- JWT validated during connection handshake
- Token passed via query parameter or first message
- Connection rejected if token invalid/expired
- Tenant context established from token claims

### OAuth/Social Login
- Out of scope until after first production release
- When implemented: OAuth 2.0 with PKCE

### MFA (Optional v1)
- TOTP-based (Google Authenticator compatible)
- Recovery codes: 10 single-use codes
- Backup: Email/SMS verification

## Password Policy

| Requirement | Value |
|-------------|-------|
| Minimum length | 12 characters |
| Complexity | Not enforced (length > complexity) |
| Hashing | Argon2id (via argon2-cffi) |
| Breach checking | Optional (Have I Been Pwned API) |
| Reuse prevention | Last 5 passwords |
| Expiry | None (NIST recommends against forced rotation) |

### Password Hashers
```python
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
]
```

## Rate Limiting

| Endpoint | Limit | Window |
|----------|-------|--------|
| Login | 5 attempts | 5 minutes |
| Password reset | 3 requests | 1 hour |
| Email verification | 3 requests | 1 hour |
| API (authenticated) | 1000 requests | 1 hour |
| API (anonymous) | 100 requests | 1 hour |

### Account Lockout
- Threshold: 5 failed login attempts
- Duration: 30 minutes
- Progressive: Doubles after each lockout
- Notification: Email sent to account owner

## Data Protection

### Encryption in Transit
- TLS 1.2 minimum (TLS 1.3 preferred)
- HSTS enabled with preload
- Certificate: Valid, from trusted CA

```python
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

### Encryption at Rest
- Database: PostgreSQL native encryption or disk-level
- Backups: Encrypted before storage
- Sensitive fields: Application-level encryption for PII if required

### Secrets Management
- Environment variables for configuration
- Never commit secrets to version control
- Production: Use secrets manager (AWS Secrets Manager, HashiCorp Vault)
- `.env` files excluded from git (`.gitignore`)

## Audit Logging

### AuditEvent Model
```python
class AuditEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    tenant_id = models.UUIDField(db_index=True)
    user_id = models.UUIDField(null=True, db_index=True)
    action = models.CharField(max_length=100)
    resource_type = models.CharField(max_length=100)
    resource_id = models.CharField(max_length=255)
    changes = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)
    correlation_id = models.UUIDField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant_id", "created_at"]),
            models.Index(fields=["user_id", "created_at"]),
        ]
```

### Audit Policy
- **Immutable**: Append-only, no updates or deletes
- **Access-controlled**: Read access restricted to admins
- **Retention**: Defined per data classification (minimum 1 year for financial)
- **Events logged**:
  - Authentication (login, logout, failed attempts)
  - Authorization changes (role assignments)
  - Data access (sensitive reads)
  - Data mutations (create, update, delete)
  - Admin actions (all)

## Observability and Correlation

### Request Correlation
- Every request gets a unique `correlation_id`
- Passed to all downstream services
- Included in logs, errors, and responses
- Format: UUID v4

### Logging Security
- No PII in logs (email, names, addresses)
- No credentials or tokens
- No financial amounts in plaintext
- Correlation ID on every log entry
- Structured JSON format (machine-parseable)

### Error Handling
- Generic error messages to users
- Detailed errors in logs only
- No stack traces in production responses
- Sentry for error aggregation

## Security Headers

```python
# Django settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True

# Additional headers via middleware
Content-Security-Policy: default-src 'self'
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

## Input Validation

- Validate all external inputs at system boundaries
- Use Django forms/DRF serializers for validation
- Parameterized queries only (no raw SQL with user input)
- File upload: Type validation, size limits, malware scanning
- URL parameters: Whitelist allowed values

## Dependency Security

- `pip-audit` or `safety` in CI pipeline
- Dependabot/Renovate for automated updates
- Security advisories monitored
- Quarterly dependency review

## Incident Response

### Contact
- Security issues: security@<domain>.com
- Response SLA: 24 hours for critical, 72 hours for others

### Severity Levels
| Level | Description | Response |
|-------|-------------|----------|
| Critical | Active exploitation, data breach | Immediate |
| High | Exploitable vulnerability | 24 hours |
| Medium | Requires specific conditions | 1 week |
| Low | Defense in depth | Next release |

## Compliance Considerations

### Data Privacy (B2C)
- User data export (GDPR Article 15)
- User data deletion (GDPR Article 17)
- Consent management
- Privacy policy required

### Financial Data
- Immutable transaction records
- Audit trail for all changes
- Data retention per jurisdiction
- Encryption requirements met
