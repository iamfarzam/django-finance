# B2C SaaS Product Baseline

This document defines the product, growth, and operational baseline for a production-ready B2C SaaS application. It complements the technical baseline with product strategy, monetization, and growth considerations.

> **Audience**: Founders, product managers, and engineers building B2C SaaS products.

---

## Table of Contents

1. [Product Foundations](#1-product-foundations)
2. [Technical Architecture](#2-technical-architecture)
3. [Authentication and User Management](#3-authentication-and-user-management)
4. [Payments and Monetization](#4-payments-and-monetization)
5. [Security and Compliance](#5-security-and-compliance)
6. [Analytics and Metrics](#6-analytics-and-metrics)
7. [UX, Onboarding, and Retention](#7-ux-onboarding-and-retention)
8. [Operations and Reliability](#8-operations-and-reliability)
9. [Growth and Experimentation](#9-growth-and-experimentation)
10. [Launch Checklist and Risks](#10-launch-checklist-and-risks)

---

## 1. Product Foundations

### Core Value Proposition

Define your value proposition in one sentence:

> **Template**: "We help [target user] to [solve problem] by [unique approach], so they can [desired outcome]."

**Example for Finance App**:
> "We help individuals track their complete financial picture by automatically organizing income, expenses, assets, and debts in one place, so they can make confident money decisions."

### Target User Definition

Create a specific user persona, not a demographic:

| Attribute | Definition |
|-----------|------------|
| **Who** | Specific role/situation (not age/gender) |
| **Pain** | The problem they feel acutely |
| **Current Solution** | What they do today (spreadsheets, nothing, competitor) |
| **Trigger** | What makes them search for a solution |
| **Success** | How they measure if your product works |

**Anti-pattern**: "Anyone who wants to manage money" → Too broad, leads to feature bloat.

### Primary User Journeys

Define 3-5 core journeys that deliver value:

| Journey | Entry Point | Success Moment | Time to Value |
|---------|-------------|----------------|---------------|
| First Value | Signup | Sees first insight | < 5 minutes |
| Core Loop | Dashboard | Completes key action | Daily/Weekly |
| Expansion | Settings | Upgrades or invites | Week 2-4 |

### Activation Moment

The activation moment is when users first experience real value. Define it precisely:

```
Activation = [Specific Action] within [Time Window]

Example: "User adds 3+ transactions within first 7 days"
```

**Why it matters**: Everything in onboarding should drive toward this moment.

### MVP vs Day-One Non-Negotiables

| Category | MVP (Can Ship Without) | Non-Negotiable (Must Have) |
|----------|------------------------|---------------------------|
| Features | Advanced reports, integrations | Core value loop complete |
| Auth | Social login, SSO | Email/password, password reset |
| Payments | Annual plans, enterprise | Monthly subscription, trial |
| Security | SOC2, penetration test | HTTPS, password hashing, GDPR basics |
| Mobile | Native apps | Responsive web |
| Support | Phone, chat | Email, help docs |
| Analytics | Advanced cohorts | Basic funnel tracking |

**Opinion**: Ship with less. The features you think are essential rarely are. The core value loop, working reliably, matters more than feature count.

---

## 2. Technical Architecture

### Recommended Stack (Small Team)

| Layer | Recommendation | Rationale |
|-------|---------------|-----------|
| **Frontend** | React/Next.js or Django Templates | SSR for SEO, fast initial load |
| **Backend** | Django + DRF | Batteries included, fast development |
| **Database** | PostgreSQL | Reliable, scalable, great ecosystem |
| **Cache** | Redis | Sessions, cache, real-time |
| **Background** | Celery | Reliable task processing |
| **Search** | PostgreSQL FTS → Elasticsearch | Start simple, migrate when needed |
| **Files** | S3/CloudFlare R2 | Cheap, reliable object storage |
| **Hosting** | Railway/Render → AWS/GCP | Start managed, migrate for scale |

### Architecture Principles

```
┌─────────────────────────────────────────────────────────────┐
│                     CDN (CloudFlare)                        │
│                   Static assets, caching                    │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Load Balancer                            │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Web App    │    │   Web App    │    │   Web App    │
│   (Daphne)   │    │   (Daphne)   │    │   (Daphne)   │
└──────────────┘    └──────────────┘    └──────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  PostgreSQL  │    │    Redis     │    │   Workers    │
│   (Primary)  │    │   (Cache)    │    │   (Celery)   │
└──────────────┘    └──────────────┘    └──────────────┘
```

### Scalability Stages

| Stage | Users | Focus | Infrastructure |
|-------|-------|-------|----------------|
| **0-1K** | Early | Ship fast, learn | Single server, managed DB |
| **1K-10K** | Growth | Reliability | Load balancer, DB replicas |
| **10K-100K** | Scale | Performance | CDN, caching, queues |
| **100K+** | Optimize | Efficiency | Microservices, specialized DBs |

**Opinion**: Don't over-engineer for scale you don't have. A single well-configured server handles more than you think.

### API Design Best Practices

```python
# Versioned endpoints
/api/v1/transactions/

# Consistent response format
{
    "data": { ... },
    "meta": { "pagination": { ... } },
    "error": null
}

# Idempotency for writes
POST /api/v1/transactions/
Header: Idempotency-Key: <uuid>

# Cursor pagination for lists
GET /api/v1/transactions/?cursor=<token>&limit=20
```

### Environment Setup

| Environment | Purpose | Data | Access |
|-------------|---------|------|--------|
| **Local** | Development | Fake/seed data | Developer only |
| **Staging** | Testing | Anonymized prod data | Team |
| **Production** | Live users | Real data | Restricted |

**Critical**: Never use production data in non-production environments without anonymization.

---

## 3. Authentication and User Management

### Authentication Methods (Priority Order)

| Method | Priority | Implementation |
|--------|----------|----------------|
| Email + Password | P0 (MVP) | Django auth + Argon2 |
| Email Magic Link | P1 | Reduces friction |
| Google OAuth | P1 | Highest conversion |
| Apple Sign-In | P2 | Required for iOS |
| SSO/SAML | P3 | Enterprise only |

### Signup Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Landing   │───▶│   Signup    │───▶│   Verify    │───▶│  Onboarding │
│    Page     │    │    Form     │    │   Email     │    │    Flow     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │ Social Auth │
                   │  (Google)   │
                   └─────────────┘
```

**Signup Form Fields**:
- Email (required)
- Password (required, 12+ chars)
- Terms acceptance checkbox (required)
- Marketing opt-in checkbox (optional, unchecked by default)

**Anti-patterns**:
- Requiring name during signup (ask later)
- Phone number during signup (friction)
- Email confirmation before any value (delay activation)

### Login Flow

```python
# Rate limiting
MAX_ATTEMPTS = 5
LOCKOUT_DURATION = 30 minutes
PROGRESSIVE_LOCKOUT = True  # Doubles each time

# Session management
SESSION_DURATION = 14 days
REMEMBER_ME_DURATION = 30 days
CONCURRENT_SESSIONS = Unlimited (B2C)
```

### Account Lifecycle

| Stage | Trigger | Actions |
|-------|---------|---------|
| **Created** | Signup | Send welcome email, start trial |
| **Verified** | Email confirmed | Full access enabled |
| **Active** | Regular usage | Normal state |
| **Inactive** | 30 days no login | Re-engagement email |
| **Dormant** | 90 days no login | Reduce resources, reminder |
| **Churned** | Subscription cancelled | Exit survey, win-back flow |
| **Deleted** | User request | 30-day grace, then hard delete |

### Password Reset Flow

```
Request ──▶ Email with token ──▶ Reset form ──▶ Confirm + Login

Token expiry: 1 hour
One-time use: Yes
Invalidate other sessions: Optional (offer choice)
```

### Roles and Permissions (B2C)

For B2C, keep it simple:

| Role | Description | Typical Access |
|------|-------------|----------------|
| **User** | Standard account | Own data only |
| **Premium** | Paid subscriber | Own data + premium features |
| **Admin** | Super admin (internal) | All data (support purposes) |

**Opinion**: Avoid complex permission systems for B2C. If you need them, you might be building B2B.

---

## 4. Payments and Monetization

### Pricing Models

| Model | Best For | Pros | Cons |
|-------|----------|------|------|
| **Freemium** | Viral products | Growth, low friction | Conversion challenge |
| **Free Trial** | High-value products | Qualified leads | Time pressure |
| **Paid Only** | Niche/premium | Simple, filters tire-kickers | Slower growth |

**Recommendation for Finance App**: Free trial (14 days) with freemium fallback.

### Pricing Tiers

| Tier | Price | Target | Features |
|------|-------|--------|----------|
| **Free** | $0 | Casual users | Core features, limited history |
| **Pro** | $9/mo | Active users | Full history, exports, categories |
| **Premium** | $19/mo | Power users | Unlimited accounts, reports, API |

**Pricing Psychology**:
- Annual discount: 20% (2 months free)
- Show monthly price even for annual
- Default to annual (but allow monthly)
- No enterprise tier for B2C

### Payment Provider

**Recommendation**: Stripe (or Paddle for tax simplification)

| Feature | Stripe | Paddle | LemonSqueezy |
|---------|--------|--------|--------------|
| Ease of setup | Medium | Easy | Easy |
| Tax handling | Manual/Stripe Tax | Automatic (MoR) | Automatic |
| Fees | 2.9% + $0.30 | 5% + $0.50 | 5% + $0.50 |
| Control | Full | Limited | Limited |

### Subscription States

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ Trialing│───▶│ Active  │───▶│Past Due │───▶│Cancelled│
└─────────┘    └─────────┘    └─────────┘    └─────────┘
     │              │              │              │
     │              ▼              │              ▼
     │         ┌─────────┐        │         ┌─────────┐
     └────────▶│  Free   │◀───────┘         │ Churned │
               └─────────┘                  └─────────┘
```

### Critical Payment Edge Cases

| Scenario | Handling |
|----------|----------|
| **Payment fails** | 3 retry attempts over 7 days, then downgrade |
| **Card expires** | Email reminder 7 days before, retry with Stripe |
| **Upgrade mid-cycle** | Prorate immediately |
| **Downgrade** | Apply at period end |
| **Cancel** | Access until period end, offer pause option |
| **Refund** | Pro-rate, automate for < 7 days |
| **Dispute** | Immediate evidence submission, don't fight small amounts |

### Webhooks to Handle

```python
CRITICAL_WEBHOOKS = [
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted",
    "invoice.paid",
    "invoice.payment_failed",
    "customer.updated",
    "charge.dispute.created",
]
```

---

## 5. Security and Compliance

### Security Baseline

| Layer | Requirement | Implementation |
|-------|-------------|----------------|
| **Transport** | HTTPS everywhere | TLS 1.2+, HSTS |
| **Authentication** | Strong passwords | Argon2, 12+ chars |
| **Sessions** | Secure cookies | HttpOnly, Secure, SameSite |
| **Data** | Encryption at rest | Database/disk encryption |
| **Secrets** | No hardcoding | Environment variables, secrets manager |
| **Dependencies** | No known vulns | Automated scanning, updates |
| **Input** | Validation | Parameterized queries, sanitization |
| **Output** | Escaping | XSS prevention |

### Authentication Security

```python
# Password requirements
MIN_LENGTH = 12
REQUIRE_COMPLEXITY = False  # Length > complexity
CHECK_BREACHED = True  # Have I Been Pwned API
HASH_ALGORITHM = "Argon2id"

# Rate limiting
LOGIN_RATE_LIMIT = "5/5m"  # 5 attempts per 5 minutes
LOCKOUT_THRESHOLD = 5
LOCKOUT_DURATION_MINUTES = 30

# Session security
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = True
```

### GDPR Compliance Checklist

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| **Consent** | Explicit opt-in for marketing | ☐ |
| **Right to Access** | Data export feature | ☐ |
| **Right to Rectification** | Profile editing | ☐ |
| **Right to Erasure** | Account deletion | ☐ |
| **Right to Portability** | JSON/CSV export | ☐ |
| **Data Minimization** | Collect only needed data | ☐ |
| **Privacy Policy** | Clear, accessible | ☐ |
| **Cookie Consent** | Banner with choices | ☐ |
| **Breach Notification** | Process in place | ☐ |
| **DPA with Processors** | Signed agreements | ☐ |

### CCPA Compliance (California)

| Requirement | Implementation |
|-------------|----------------|
| **Right to Know** | Disclosure of data collected |
| **Right to Delete** | Account deletion |
| **Right to Opt-Out** | "Do Not Sell" link (if applicable) |
| **Non-Discrimination** | Same service regardless of opt-out |

### Logging and Audit

```python
# What to log
AUDIT_EVENTS = [
    "user.signup",
    "user.login",
    "user.logout",
    "user.password_changed",
    "user.email_changed",
    "user.deleted",
    "subscription.created",
    "subscription.cancelled",
    "data.exported",
    "admin.accessed_user",
]

# What NOT to log
NEVER_LOG = [
    "passwords",
    "credit_card_numbers",
    "full_ssn",
    "api_keys",
    "session_tokens",
]
```

### Incident Response

```
Detection ──▶ Triage ──▶ Containment ──▶ Eradication ──▶ Recovery ──▶ Lessons

Timeline:
- Detection: Automated monitoring
- Triage: Within 1 hour
- Containment: Within 4 hours
- User notification: Within 72 hours (GDPR)
```

---

## 6. Analytics and Metrics

### Core B2C SaaS Metrics

| Metric | Formula | Target | Frequency |
|--------|---------|--------|-----------|
| **MAU** | Unique users/month | Growth | Weekly |
| **Activation Rate** | Activated / Signups | > 40% | Weekly |
| **Day 1 Retention** | D1 active / Signups | > 40% | Daily |
| **Day 7 Retention** | D7 active / Signups | > 20% | Weekly |
| **Day 30 Retention** | D30 active / Signups | > 10% | Monthly |
| **Trial-to-Paid** | Converted / Trials | > 5% | Weekly |
| **Monthly Churn** | Churned / Start MRR | < 5% | Monthly |
| **MRR** | Monthly recurring revenue | Growth | Weekly |
| **LTV** | Average revenue / user lifetime | > 3x CAC | Monthly |
| **CAC** | Acquisition cost / Customers | < LTV/3 | Monthly |

### Metrics Hierarchy

```
                    ┌─────────────────┐
                    │      MRR        │  ◀── North Star
                    └────────┬────────┘
                             │
           ┌─────────────────┼─────────────────┐
           ▼                 ▼                 ▼
    ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
    │  New MRR    │   │  Expansion  │   │   Churn     │
    └──────┬──────┘   └──────┬──────┘   └──────┬──────┘
           │                 │                 │
    ┌──────┴──────┐   ┌──────┴──────┐   ┌──────┴──────┐
    │  Signups    │   │   Upgrades  │   │  Retention  │
    │  Activation │   │   Add-ons   │   │  Engagement │
    │  Conversion │   │             │   │             │
    └─────────────┘   └─────────────┘   └─────────────┘
```

### Event Tracking

**Critical Events to Track**:

```python
SIGNUP_EVENTS = [
    "signup_started",
    "signup_completed",
    "email_verified",
    "onboarding_started",
    "onboarding_completed",
]

ACTIVATION_EVENTS = [
    "first_transaction_added",
    "third_transaction_added",  # Activation threshold
    "first_category_created",
    "first_report_viewed",
]

ENGAGEMENT_EVENTS = [
    "session_started",
    "dashboard_viewed",
    "transaction_added",
    "report_generated",
    "export_downloaded",
]

MONETIZATION_EVENTS = [
    "pricing_page_viewed",
    "trial_started",
    "checkout_started",
    "checkout_completed",
    "subscription_cancelled",
]
```

### Analytics Stack

| Purpose | Tool | Why |
|---------|------|-----|
| **Product Analytics** | Mixpanel / Amplitude / PostHog | Event tracking, funnels |
| **Web Analytics** | Plausible / Fathom | Privacy-first, simple |
| **Error Tracking** | Sentry | Error aggregation |
| **Session Recording** | PostHog / Hotjar | UX debugging |
| **Revenue** | Stripe Dashboard / Baremetrics | MRR tracking |

**Opinion**: Start with PostHog (open-source, all-in-one) or Mixpanel (best funnels). Add specialized tools only when needed.

### Dashboard Signals

**Daily Dashboard**:
- Signups today
- Activations today
- Trials started
- Revenue today

**Weekly Dashboard**:
- WAU trend
- Activation rate
- Trial conversion rate
- Churn events

**Monthly Dashboard**:
- MRR and growth rate
- LTV and CAC
- Cohort retention
- Feature adoption

---

## 7. UX, Onboarding, and Retention

### First-Time User Experience

**The Critical First 5 Minutes**:

```
Landing ──▶ Signup ──▶ Onboarding ──▶ First Value ──▶ Aha Moment
  30s        60s         120s          60s           30s
```

**Rules**:
1. Time to first value < 5 minutes
2. No dead ends (always clear next action)
3. Show progress (steps, progress bars)
4. Allow skipping (but track it)
5. Celebrate wins (confetti is fine, be genuine)

### Onboarding Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     Onboarding Flow                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Step 1: Welcome + Value Reminder                          │
│  "Let's get your finances organized in 2 minutes"          │
│                                                             │
│  Step 2: Quick Win                                          │
│  "Add your first transaction" (or import)                  │
│                                                             │
│  Step 3: Personalization                                    │
│  "What's your main financial goal?"                        │
│                                                             │
│  Step 4: Setup Complete                                     │
│  "You're all set! Here's your dashboard"                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Progressive Disclosure

| Stage | Show | Hide |
|-------|------|------|
| **Day 1** | Core features only | Advanced settings |
| **Day 3** | Feature hints | Power user tools |
| **Day 7** | Full feature set | Nothing |
| **Day 14** | Upgrade prompts | - |

### Email Sequences

**Onboarding Sequence**:

| Day | Email | Goal |
|-----|-------|------|
| 0 | Welcome + Quick Start | Set expectations |
| 1 | Did you complete setup? | Activation nudge |
| 3 | Feature tip #1 | Education |
| 5 | Success story | Social proof |
| 7 | Check-in | Engagement check |
| 10 | Feature tip #2 | Deeper engagement |
| 12 | Trial ending soon | Conversion prep |
| 13 | Last day of trial | Urgency |
| 14 | Trial ended | Final conversion |

**Re-engagement Sequence**:

| Trigger | Email | Goal |
|---------|-------|------|
| 7 days inactive | "We miss you" | Return |
| 14 days inactive | Feature update | New reason to return |
| 30 days inactive | "Is everything okay?" | Win-back |

### Retention Mechanics

| Mechanic | Implementation | Impact |
|----------|----------------|--------|
| **Streaks** | "5-day tracking streak!" | Daily engagement |
| **Achievements** | "First month complete!" | Milestone celebration |
| **Reminders** | "Don't forget to log today" | Habit formation |
| **Reports** | "Your weekly summary" | Regular value delivery |
| **Social** | "Share your progress" | Viral + commitment |

### Notification Strategy

| Channel | When to Use | Frequency Limit |
|---------|-------------|-----------------|
| **In-app** | Feature updates, tips | Unlimited (non-intrusive) |
| **Email** | Summaries, important updates | 2-3/week max |
| **Push** | Time-sensitive, user action | 1/day max |
| **SMS** | Security only | Auth codes only |

---

## 8. Operations and Reliability

### Monitoring Stack

| Layer | Tool | What to Monitor |
|-------|------|-----------------|
| **Uptime** | UptimeRobot / Better Stack | Endpoint availability |
| **Errors** | Sentry | Application errors |
| **Performance** | Sentry / DataDog | Response times |
| **Logs** | Logtail / Papertrail | Application logs |
| **Infrastructure** | Provider dashboard | CPU, memory, disk |
| **Database** | pganalyze / Provider | Query performance |

### Alerting Rules

| Metric | Warning | Critical | Response |
|--------|---------|----------|----------|
| Error rate | > 1% | > 5% | Investigate |
| P95 latency | > 500ms | > 2s | Optimize |
| CPU usage | > 70% | > 90% | Scale |
| Memory usage | > 80% | > 95% | Scale/fix leak |
| Disk usage | > 70% | > 90% | Expand/cleanup |
| Failed jobs | > 10/hr | > 100/hr | Fix or pause |
| 5xx errors | > 10/hr | > 100/hr | Immediate fix |

### Uptime Targets

| Tier | Uptime | Downtime/Month | Appropriate For |
|------|--------|----------------|-----------------|
| **99%** | 7.3 hours | Early startup | MVP |
| **99.9%** | 43 minutes | Growing product | Post-PMF |
| **99.99%** | 4.3 minutes | Mature product | At scale |

**Opinion**: Target 99.9% but don't obsess. Users forgive occasional downtime if you communicate well.

### Backup Strategy

| Data | Frequency | Retention | Test Frequency |
|------|-----------|-----------|----------------|
| Database | Continuous (WAL) | 30 days | Monthly |
| Daily snapshots | Daily | 7 days | Monthly |
| Weekly snapshots | Weekly | 4 weeks | Quarterly |
| Monthly snapshots | Monthly | 12 months | Quarterly |
| User uploads | Real-time (S3) | Indefinite | Quarterly |

### Disaster Recovery

| Scenario | RTO | RPO | Procedure |
|----------|-----|-----|-----------|
| Server failure | 5 min | 0 | Auto-failover |
| Database corruption | 1 hour | 1 hour | Restore from backup |
| Region outage | 4 hours | 1 hour | Failover to DR region |
| Security breach | 2 hours | 0 | Incident playbook |

### Customer Support

**Support Tiers**:

| Tier | Channel | SLA | Staffing |
|------|---------|-----|----------|
| **Free** | Email, Help docs | 48 hours | Async |
| **Pro** | Email, Chat | 24 hours | Business hours |
| **Premium** | Priority email | 4 hours | Extended hours |

**Support Stack**:
- **Help Desk**: Intercom / Zendesk / Help Scout
- **Knowledge Base**: Built-in or Notion
- **Chat**: Intercom / Crisp (for Pro+)

**Self-Service First**:
- Comprehensive FAQ
- Searchable help docs
- Video tutorials for complex features
- In-app tooltips

---

## 9. Growth and Experimentation

### A/B Testing Foundations

**What to Test (Priority Order)**:

| Priority | Test | Impact |
|----------|------|--------|
| P0 | Pricing page | Revenue |
| P0 | Signup flow | Conversion |
| P1 | Onboarding steps | Activation |
| P1 | Email subject lines | Open rates |
| P2 | Feature placement | Engagement |
| P2 | Copy variations | Click-through |

**Testing Rules**:
1. One change per test
2. Minimum 1,000 users per variant
3. Run for at least 2 weeks
4. 95% statistical significance
5. Document everything

### Feature Flags

**Implementation**:

```python
# Feature flag structure
FEATURE_FLAGS = {
    "new_dashboard": {
        "enabled": True,
        "rollout_percentage": 25,
        "user_segments": ["beta_users"],
        "start_date": "2026-02-01",
    },
}

# Usage
if feature_enabled("new_dashboard", user):
    show_new_dashboard()
else:
    show_old_dashboard()
```

**Rollout Strategy**:

| Stage | Audience | Duration | Goal |
|-------|----------|----------|------|
| **Alpha** | Internal team | 1 week | Bug finding |
| **Beta** | Opt-in users | 2 weeks | Feedback |
| **Limited** | 10% of users | 1 week | Metrics validation |
| **Gradual** | 25% → 50% → 100% | 2 weeks | Monitor for issues |

### User Feedback Loops

| Method | When | Frequency | Tool |
|--------|------|-----------|------|
| **NPS Survey** | After 30 days, then quarterly | Quarterly | Delighted / in-app |
| **In-app Feedback** | Always available | Continuous | Custom / Canny |
| **Exit Survey** | On cancellation | Every cancel | Custom |
| **User Interviews** | Ongoing | 5/month | Calendly + Zoom |
| **Feature Requests** | Always open | Continuous | Canny / Productboard |

**Feedback Processing**:

```
Collect ──▶ Categorize ──▶ Prioritize ──▶ Build ──▶ Close Loop

Close Loop = Tell users what you built from their feedback
```

### Growth Channels (B2C)

| Channel | Cost | Time to Impact | Best For |
|---------|------|----------------|----------|
| **SEO** | Low | 6+ months | Long-term |
| **Content** | Medium | 3+ months | Authority |
| **Social** | Low | Ongoing | Community |
| **Referral** | Low | Immediate | Viral products |
| **Paid Ads** | High | Immediate | Testing, scaling |
| **Partnerships** | Medium | 3+ months | Distribution |

---

## 10. Launch Checklist and Risks

### Pre-Launch Checklist

#### Product
- [ ] Core user journey works end-to-end
- [ ] Mobile responsive
- [ ] Error states handled gracefully
- [ ] Loading states present
- [ ] Empty states designed
- [ ] Offline handling (if applicable)

#### Technical
- [ ] HTTPS enabled
- [ ] Database backups configured
- [ ] Monitoring and alerting set up
- [ ] Error tracking configured
- [ ] Performance baseline established
- [ ] Security headers configured
- [ ] Rate limiting enabled

#### Legal/Compliance
- [ ] Privacy policy published
- [ ] Terms of service published
- [ ] Cookie consent implemented
- [ ] GDPR data export works
- [ ] Account deletion works
- [ ] Payment terms clear

#### Growth
- [ ] Analytics tracking verified
- [ ] Key funnels instrumented
- [ ] Email sequences ready
- [ ] Social sharing works
- [ ] SEO basics (title, meta, sitemap)

#### Operations
- [ ] Support email works
- [ ] Help documentation exists
- [ ] FAQ covers common questions
- [ ] Feedback mechanism in place
- [ ] On-call rotation defined

### Common B2C SaaS Mistakes

| Mistake | Why It Happens | Prevention |
|---------|----------------|------------|
| **Building too much** | Fear of launching | Define MVP ruthlessly |
| **Ignoring activation** | Focus on signups | Track activation metric |
| **No pricing validation** | Assuming users will pay | Test willingness early |
| **Over-engineering** | Fear of scale | Solve today's problems |
| **Ignoring churn** | Focus on acquisition | Exit surveys, retention work |
| **No feedback loop** | Building in isolation | Talk to users weekly |
| **Premature optimization** | Exciting but distracting | 80/20 rule |
| **Ignoring mobile** | Desktop-first dev | Mobile-first design |
| **Slow onboarding** | Feature-first thinking | Time to value < 5 min |
| **No monetization clarity** | "We'll figure it out" | Pricing from day 1 |

### First 90 Days Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Low signup volume** | High | High | Have acquisition plan, paid backup |
| **Low activation** | High | Critical | Instrument heavily, iterate fast |
| **Poor trial conversion** | Medium | High | Optimize onboarding, pricing |
| **Technical issues** | Medium | Medium | Monitoring, on-call rotation |
| **Negative reviews** | Medium | High | Responsive support, fast fixes |
| **Competitor response** | Low | Medium | Focus on your users |
| **Scaling issues** | Low | Medium | Performance baseline, alerts |
| **Security incident** | Low | Critical | Security baseline, response plan |

### Week 1 Focus

| Day | Focus | Actions |
|-----|-------|---------|
| 1-2 | Bugs | Fix any launch bugs immediately |
| 3-4 | Feedback | Talk to every early user possible |
| 5-7 | Activation | Identify and fix activation blockers |

### Week 2-4 Focus

| Week | Focus | Metrics |
|------|-------|---------|
| 2 | Onboarding optimization | Activation rate |
| 3 | Retention signals | Day 7 retention |
| 4 | Conversion prep | Trial-to-paid signals |

### Month 2-3 Focus

| Month | Focus | Metrics |
|-------|-------|---------|
| 2 | Conversion optimization | Trial-to-paid rate |
| 3 | Retention and expansion | Churn rate, upgrades |

---

## Quick Reference

### North Star Metrics by Stage

| Stage | North Star | Why |
|-------|------------|-----|
| **Pre-launch** | Signups for waitlist | Demand validation |
| **Launch** | Activation rate | Value delivery |
| **Growth** | Weekly active users | Engagement |
| **Monetization** | MRR | Business viability |
| **Scale** | Net revenue retention | Sustainable growth |

### Decision Framework

```
Is this necessary for the core value loop?
├── Yes ──▶ Build it
└── No
    └── Does it directly drive a key metric?
        ├── Yes ──▶ Prioritize based on impact
        └── No ──▶ Add to backlog, revisit later
```

### Golden Rules

1. **Ship fast, iterate faster** — Launch imperfect, improve continuously
2. **Instrument everything** — You can't improve what you don't measure
3. **Talk to users** — 5 user calls/week minimum
4. **Focus on activation** — It's the most important metric early on
5. **Retention over acquisition** — Easier to keep users than find new ones
6. **Simple pricing** — Confusion kills conversion
7. **Self-service first** — Scale support through documentation
8. **Mobile matters** — Especially for B2C
9. **Speed is a feature** — Performance = conversion
10. **Close the loop** — Tell users what you built from their feedback
