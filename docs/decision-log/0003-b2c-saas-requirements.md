# ADR-0003: B2C SaaS Product Requirements

## Status
Accepted

## Date
2026-02-07

## Context

This is a B2C (Business-to-Consumer) SaaS product for personal finance management. B2C SaaS products have specific requirements that differ from B2B or internal applications:

1. **Scale**: Potentially millions of individual users
2. **Self-service**: Users onboard, manage, and troubleshoot independently
3. **Privacy**: Personal financial data requires strict protection
4. **Compliance**: GDPR, CCPA, and financial regulations
5. **Availability**: Users expect 24/7 access
6. **Experience**: Consumer-grade UX expectations

## Decision

### User Lifecycle Management

| Stage | Requirements |
|-------|-------------|
| Registration | Email verification, terms acceptance, optional profile |
| Onboarding | Guided setup, sample data option, help resources |
| Active Use | Dashboard, notifications, data export |
| Dormant | Re-engagement emails, data retention policy |
| Deletion | Right to erasure, data export, account closure |

### Data Privacy and Compliance

**GDPR Compliance**:
- Right to access (Article 15): Export all user data
- Right to rectification (Article 16): Update personal data
- Right to erasure (Article 17): Delete account and data
- Right to data portability (Article 20): Export in machine-readable format
- Consent management: Track and honor consent preferences

**Financial Data Protection**:
- Data classified as sensitive PII
- Encryption at rest and in transit
- Access logging and audit trails
- No third-party data sharing without consent
- Retention limits per data type

### Multi-Tenancy Model

For B2C, each user account is treated as a tenant:

```
User (Account) = Tenant
├── Financial Accounts
├── Transactions
├── Assets & Liabilities
└── Settings & Preferences
```

**Isolation Requirements**:
- All queries scoped to authenticated user's tenant
- No cross-tenant data leakage
- Separate encryption keys per tenant (optional, Phase 9)
- Tenant ID in all audit logs

### Self-Service Features

| Feature | Priority | Implementation |
|---------|----------|----------------|
| Password reset | Required | Email-based with secure tokens |
| Email change | Required | Verification on both addresses |
| Data export | Required | JSON/CSV download |
| Account deletion | Required | Soft delete + hard delete after grace period |
| Support tickets | Optional | Integration with help desk |
| FAQ/Help center | Required | Static content, searchable |

### Subscription and Billing

**Phase 1 (MVP)**: Free tier only
- No payment integration
- Usage limits if needed
- Upgrade prompts for future paid features

**Future Phases**:
- Stripe/payment integration
- Subscription tiers (Free, Pro, Premium)
- Usage-based billing for specific features
- Invoice generation and history

### Analytics and Metrics

**Product Metrics**:
- Daily/Monthly Active Users (DAU/MAU)
- User retention (cohort analysis)
- Feature adoption rates
- Conversion funnel (registration → activation)

**Technical Metrics**:
- Response latency (p50, p95, p99)
- Error rates by endpoint
- Database query performance
- Background job completion rates

**Privacy-Conscious Analytics**:
- No PII in analytics
- Aggregate metrics only
- User opt-out capability
- GDPR-compliant tracking

### Communication

| Type | Channel | Purpose |
|------|---------|---------|
| Transactional | Email | Verification, password reset, alerts |
| Notifications | In-app, Push, Email | Activity updates, reminders |
| Marketing | Email | Feature announcements (opt-in) |
| Support | Email, In-app | Issue resolution |

**Requirements**:
- Unsubscribe for marketing emails
- Preference center for notification types
- Email templates with consistent branding
- Delivery tracking and bounce handling

### Customer Support

**Self-Service First**:
- Comprehensive help documentation
- Searchable FAQ
- In-app tooltips and guides
- Video tutorials (future)

**Escalation Path**:
- Contact form with ticket tracking
- Email support with SLA
- Priority support for paid tiers (future)

### Feature Flags

Gradual rollout and experimentation:

```python
FEATURE_FLAGS = {
    "mfa_enabled": False,           # MFA for all users
    "dark_mode": True,              # UI dark mode
    "export_csv": True,             # CSV export capability
    "advanced_reports": False,      # Premium reporting
    "api_access": False,            # External API access
}
```

**Implementation**:
- Database-backed flags for per-user control
- Environment-based defaults
- Admin UI for flag management
- A/B testing capability (future)

### Localization (Future)

**Phase 1**: English only
**Future**:
- Multi-language support
- Currency formatting per locale
- Date/time formatting
- RTL language support

## Consequences

### Positive
- Clear roadmap for B2C-specific features
- Privacy-first design from the start
- Self-service reduces support burden
- Scalable multi-tenancy model

### Negative
- Additional complexity for data privacy compliance
- Self-service features require more upfront development
- Analytics require careful privacy considerations

### Risks
- Regulatory changes may require updates
- Scaling to millions of users requires infrastructure planning
- Customer support load if self-service is insufficient

## Implementation Notes

### Phase 2 (Foundations)
- User registration and email verification
- Basic profile management
- Password reset flow
- Tenant context middleware

### Phase 3 (Core Domain)
- Data export capability
- Account deletion flow (soft delete)
- Audit logging

### Phase 6 (Web UI)
- Help documentation
- Contact form
- Preference center

### Phase 9 (Production)
- Analytics integration
- Performance optimization for scale
- Support ticket integration

## References

- [GDPR Official Text](https://gdpr-info.eu/)
- [CCPA Overview](https://oag.ca.gov/privacy/ccpa)
- [OWASP Security Guidelines](https://owasp.org/)
