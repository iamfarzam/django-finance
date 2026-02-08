# Security Checklist

## Overview

This document provides a comprehensive security checklist for Django Finance production deployment. Review and verify each item before going live.

## Django Security Settings

### Core Security

- [x] `DEBUG = False` in production
- [x] `SECRET_KEY` is unique and stored securely (environment variable)
- [x] `ALLOWED_HOSTS` is properly configured
- [x] `CSRF_TRUSTED_ORIGINS` is set for production domain

### HTTPS/SSL

- [x] `SECURE_SSL_REDIRECT = True`
- [x] `SECURE_PROXY_SSL_HEADER` configured for reverse proxy
- [x] HSTS enabled:
  - [x] `SECURE_HSTS_SECONDS = 31536000` (1 year)
  - [x] `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`
  - [x] `SECURE_HSTS_PRELOAD = True`

### Content Security

- [x] `SECURE_CONTENT_TYPE_NOSNIFF = True`
- [x] `SECURE_BROWSER_XSS_FILTER = True`
- [x] `X_FRAME_OPTIONS = "DENY"`

### Cookie Security

- [x] `SESSION_COOKIE_SECURE = True`
- [x] `SESSION_COOKIE_HTTPONLY = True`
- [x] `SESSION_COOKIE_SAMESITE = "Lax"`
- [x] `CSRF_COOKIE_SECURE = True`
- [x] `CSRF_COOKIE_HTTPONLY = True`
- [x] `CSRF_COOKIE_SAMESITE = "Lax"`

### Database Security

- [x] `DATABASES["default"]["OPTIONS"]["sslmode"] = "require"`
- [x] Database credentials stored in environment variables
- [x] Connection pooling with health checks enabled

## Authentication Security

### Password Policy

- [x] Minimum 12 characters
- [x] CommonPasswordValidator enabled
- [x] UserAttributeSimilarityValidator enabled
- [x] NumericPasswordValidator enabled

### Password Hashing

- [x] Argon2id as primary hasher
- [x] PBKDF2 as fallback

### Account Protection

- [x] Account lockout after 5 failed attempts
- [x] Rate limiting on login endpoint (5/minute)
- [x] Rate limiting on registration (10/hour)
- [x] Rate limiting on password reset (3/hour)

### Session Security

- [x] Session stored in Redis (not database)
- [x] Session timeout: 2 weeks
- [x] Session regeneration on login

### JWT Security

- [x] Access token lifetime: 15 minutes (configurable)
- [x] Refresh token lifetime: 7 days (configurable)
- [x] Token rotation on refresh
- [x] Blacklist after rotation

## API Security

### Authentication

- [x] JWT required for API endpoints
- [x] Session auth supported for web
- [x] CORS properly configured

### Authorization

- [x] Tenant isolation enforced
- [x] Object-level permissions
- [x] Role-based access control

### Rate Limiting

- [x] Anonymous: 100/hour
- [x] Authenticated: 1000/hour
- [x] Finance operations: Custom limits
- [x] Premium users: Higher limits

### Input Validation

- [x] All inputs validated via serializers
- [x] Decimal precision enforced
- [x] Currency codes validated
- [x] UUIDs validated

## Data Protection

### Encryption

- [x] TLS 1.2+ for all connections
- [x] Database connections encrypted (SSL)
- [x] Passwords hashed with Argon2id

### Sensitive Data

- [x] No secrets in code or logs
- [x] Audit logging masks sensitive fields
- [x] Field-level permissions for premium data

### Financial Data

- [x] Decimal precision (4 decimal places)
- [x] Immutable transactions
- [x] Audit trail for all changes

## Infrastructure Security

### Database

- [ ] Regular automated backups
- [ ] Point-in-time recovery enabled
- [ ] Backup encryption enabled
- [ ] Backup access restricted

### Redis

- [x] Password authentication enabled
- [x] TLS for Redis connections (if remote)
- [ ] Memory limits configured

### Application Server

- [ ] Non-root user
- [ ] Read-only filesystem where possible
- [ ] Resource limits (CPU, memory)
- [ ] Health checks enabled

### Reverse Proxy

- [ ] Rate limiting at edge
- [ ] DDoS protection
- [ ] WAF rules configured
- [ ] Request size limits

## Monitoring & Logging

### Logging

- [x] Structured JSON logs in production
- [x] Correlation IDs for request tracing
- [x] Sensitive data masked in logs
- [x] Log rotation configured

### Audit Logging

- [x] All financial operations logged
- [x] Authentication events logged
- [x] Admin actions logged
- [x] Retention: 7 years financial, 2 years security

### Monitoring

- [ ] Error tracking (Sentry) configured
- [ ] Uptime monitoring enabled
- [ ] Performance monitoring enabled
- [ ] Alerting rules configured

## Dependency Security

### Python Dependencies

- [x] Regular dependency updates
- [x] Vulnerability scanning configured:
  - [x] Bandit (static security analysis)
  - [x] Safety (known vulnerability check)
  - [x] pip-audit (dependency audit)
- [x] Pinned versions in pyproject.toml

### Automated Security Scanning

Run security scans with:
```bash
make security          # Run all security checks
make security-bandit   # Bandit only
make security-deps     # Safety + pip-audit
make security-report   # Generate JSON/HTML reports
```

### JavaScript Dependencies

- [ ] npm audit clean
- [ ] Regular updates
- [x] Lockfile committed (package-lock.json)

## Deployment Security

### CI/CD

- [ ] Secrets in environment, not code
- [ ] Build artifacts scanned
- [ ] Automated security tests

### Container Security

- [ ] Minimal base image
- [ ] Non-root user in container
- [ ] No secrets in image
- [ ] Image scanning enabled

## Incident Response

### Preparation

- [ ] Incident response plan documented
- [ ] Contact list updated
- [ ] Runbook created

### Detection

- [ ] Log aggregation configured
- [ ] Alerting rules active
- [ ] Anomaly detection enabled

### Response

- [ ] Rollback procedure documented
- [ ] Communication templates ready
- [ ] Legal/compliance contacts listed

## Compliance

### GDPR (if applicable)

- [x] Data export capability
- [x] Data deletion capability
- [ ] Privacy policy published
- [ ] Cookie consent implemented

### Financial Regulations

- [x] Audit trail maintained
- [x] Data retention policies
- [x] Access controls documented

## OWASP Top 10 Review

| Risk | Status | Notes |
|------|--------|-------|
| A01: Broken Access Control | ✅ | Tenant isolation, RBAC, object permissions |
| A02: Cryptographic Failures | ✅ | TLS, Argon2id, secure cookies |
| A03: Injection | ✅ | Django ORM, parameterized queries |
| A04: Insecure Design | ✅ | Clean architecture, input validation |
| A05: Security Misconfiguration | ✅ | Production settings reviewed |
| A06: Vulnerable Components | ⚠️ | Need regular scanning |
| A07: Auth Failures | ✅ | Rate limiting, lockout, strong passwords |
| A08: Data Integrity Failures | ✅ | Signed JWTs, CSRF protection |
| A09: Logging Failures | ✅ | Structured logging, audit trail |
| A10: SSRF | ✅ | No external URL fetching |

## Pre-Production Checklist

Before deploying to production, verify:

1. [ ] All security settings enabled
2. [ ] SSL certificate installed and valid
3. [ ] Database backups configured
4. [ ] Monitoring and alerting active
5. [ ] Secrets rotated from development
6. [ ] Admin accounts secured
7. [ ] Rate limiting tested
8. [ ] Error pages configured (no debug info)
9. [ ] Logging configured and tested
10. [ ] Incident response plan ready

## Regular Security Tasks

### Daily
- Review error logs for anomalies
- Check monitoring dashboards

### Weekly
- Review failed login attempts
- Check rate limiting effectiveness

### Monthly
- Review audit logs
- Update dependencies
- Review access permissions

### Quarterly
- Security dependency scan
- Access review
- Backup restore test

### Annually
- Full security audit
- Penetration testing
- Compliance review
