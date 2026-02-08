# Support & Maintenance Policy

## Overview

This document outlines the support and maintenance policy for Django Finance, including version lifecycle, support tiers, and end-of-life procedures.

## Version Support Lifecycle

### Support Phases

| Phase | Duration | Description |
|-------|----------|-------------|
| **Active** | 12 months | Full support: features, bugs, security |
| **Maintenance** | 6 months | Bug fixes and security patches only |
| **End of Life** | - | No support, upgrade required |

### Timeline

```
Release ──────────────────────────────────────────────► EOL
   │                                                      │
   ├─────── Active Support (12 months) ────────┤         │
   │                                           │         │
   │                               ├─── Maintenance (6 months) ───┤
   │                               │                              │
   v                               v                              v
 v1.0.0                     +12 months                     +18 months
```

### Version Support Matrix

| Version | Release Date | Active Until | EOL Date | Status |
|---------|--------------|--------------|----------|--------|
| 0.1.0 | TBD | TBD | TBD | Development |

## Support Tiers

### Community Support (Free)

Available to all users:

- GitHub Issues for bug reports
- GitHub Discussions for questions
- Documentation and guides
- Community forums

**Response Time**: Best effort, no SLA

### Standard Support (Paid - Future)

For paying customers:

- Email support
- Bug fixes prioritized
- Security patches
- Upgrade assistance

**Response Time**:
- Critical: 4 hours
- High: 8 hours
- Medium: 24 hours
- Low: 72 hours

### Enterprise Support (Paid - Future)

For enterprise customers:

- Dedicated support channel
- Phone support
- Custom SLAs
- Dedicated account manager
- Professional services

**Response Time**:
- Critical: 1 hour
- High: 4 hours
- Medium: 8 hours
- Low: 24 hours

## Issue Classification

### Severity Levels

| Level | Description | Examples |
|-------|-------------|----------|
| **Critical** | Service down or data loss | Complete outage, security breach |
| **High** | Major feature broken | Cannot create transactions |
| **Medium** | Feature degraded | Slow performance, UI issues |
| **Low** | Minor issue | Cosmetic bugs, typos |

### Priority Matrix

| Severity | Active Version | Maintenance Version |
|----------|----------------|---------------------|
| Critical | Immediate | Immediate |
| High | Next release | Best effort |
| Medium | Planned release | Not guaranteed |
| Low | Backlog | Not supported |

## Security Support

### Vulnerability Handling

1. **Report**: Security issues via security@example.com
2. **Assess**: Severity assessment within 24 hours
3. **Fix**: Patch development (timeline based on severity)
4. **Release**: Security advisory and patch
5. **Disclose**: Public disclosure after patch available

### Security Patch Policy

| Severity | Active Version | Maintenance Version |
|----------|----------------|---------------------|
| Critical | Immediate | Immediate |
| High | Within 7 days | Within 14 days |
| Medium | Next release | Best effort |
| Low | Planned release | Not guaranteed |

### Security Advisories

Security advisories will be published:
- GitHub Security Advisories
- CHANGELOG.md
- Email to registered users (critical only)

## Upgrade Policy

### Upgrade Path

We support direct upgrades between:
- Sequential minor versions (1.0 → 1.1 → 1.2)
- One major version jump (1.x → 2.x)

For larger jumps, sequential upgrades are required.

### Deprecation Policy

1. **Announce**: Deprecation notice in release notes
2. **Document**: Migration guide provided
3. **Warning**: Runtime warnings for 2 minor versions
4. **Remove**: Feature removed in next major version

### Breaking Changes

Breaking changes will:
- Only occur in major versions
- Be documented in CHANGELOG.md
- Include migration guide
- Have deprecation warnings in prior release

## Maintenance Procedures

### Regular Maintenance

| Task | Frequency | Description |
|------|-----------|-------------|
| Dependency updates | Monthly | Update to latest compatible versions |
| Security scanning | Weekly | Automated vulnerability scanning |
| Performance review | Quarterly | Analyze and optimize |
| Documentation review | Quarterly | Update for accuracy |

### Dependency Policy

| Dependency Type | Update Policy |
|-----------------|---------------|
| Security patches | Immediate |
| Bug fixes | Monthly |
| Minor versions | Quarterly |
| Major versions | Planned, tested |

### Django LTS Support

Django Finance follows Django's LTS release schedule:

| Django Version | Our Support |
|----------------|-------------|
| Django 5.2 LTS | Supported until April 2028 |
| Django 6.x | Will support when released |

## End of Life (EOL)

### EOL Announcement

- Announced 6 months before EOL
- Communication via:
  - GitHub release notes
  - Documentation banner
  - Email to users (if applicable)

### Post-EOL

After EOL:
- No bug fixes
- No security patches
- No support
- Repository archived (for old major versions)
- Documentation preserved but marked as EOL

### Migration Assistance

For EOL versions:
- Upgrade guide provided
- Migration scripts (if applicable)
- Community support for migration questions

## Contributing

### Bug Reports

1. Search existing issues
2. Provide minimal reproduction
3. Include version information
4. Follow issue template

### Feature Requests

1. Check roadmap and existing requests
2. Describe use case clearly
3. Be open to discussion

### Pull Requests

1. Follow contribution guidelines
2. Include tests
3. Update documentation
4. Sign CLA (if required)

## Documentation

### Documentation Types

| Type | Location | Updated |
|------|----------|---------|
| User Guide | docs/ | Each release |
| API Reference | /api/docs/ | Auto-generated |
| Changelog | CHANGELOG.md | Each release |
| Architecture | docs/ENGINEERING_BASELINE.md | Major changes |

### Documentation Support

- Documentation bugs treated as medium priority
- Community contributions welcome
- Translations (future consideration)

## Feedback

We welcome feedback on our support policy:
- GitHub Discussions
- Email: feedback@example.com

## Policy Updates

This policy may be updated:
- Changes announced in release notes
- Major changes communicated via email
- Existing versions grandfathered (support terms at release apply)

---

*Last Updated: 2026-02-08*
*Version: 1.0*
