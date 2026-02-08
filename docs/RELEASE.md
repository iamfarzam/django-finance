# Release Process

## Overview

This document describes the release process for Django Finance, including versioning, changelog management, and deployment procedures.

## Version Scheme

Django Finance follows [Semantic Versioning 2.0.0](https://semver.org/):

```
MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]
```

- **MAJOR**: Breaking changes to API or data models
- **MINOR**: New features, backward-compatible
- **PATCH**: Bug fixes, backward-compatible
- **PRERELEASE**: Alpha, beta, or release candidate (e.g., `1.0.0-alpha.1`)
- **BUILD**: Build metadata (e.g., `1.0.0+build.123`)

### Examples

| Version | Description |
|---------|-------------|
| `0.1.0` | Initial development release |
| `1.0.0` | First stable production release |
| `1.1.0` | New feature added |
| `1.1.1` | Bug fix |
| `2.0.0` | Breaking API change |
| `1.2.0-beta.1` | Beta release for testing |

## Release Types

### Major Release (X.0.0)

Includes breaking changes:
- API endpoint changes (removal, restructure)
- Database schema changes requiring migration
- Authentication/authorization changes
- Removal of deprecated features

**Process:**
1. Announce deprecations in previous minor release
2. Provide migration guide
3. Extended testing period (2+ weeks)
4. Staged rollout

### Minor Release (X.Y.0)

New features, backward-compatible:
- New API endpoints
- New optional fields
- Performance improvements
- New integrations

**Process:**
1. Feature freeze 1 week before release
2. Testing period (1 week)
3. Standard rollout

### Patch Release (X.Y.Z)

Bug fixes only:
- Security patches
- Bug fixes
- Documentation updates
- Dependency updates (non-breaking)

**Process:**
1. Minimal testing (affected areas)
2. Immediate rollout for security fixes
3. Standard rollout for other fixes

## Release Checklist

### Pre-Release

- [ ] All tests passing (`make test`)
- [ ] Security scan clean (`make security`)
- [ ] Type checking passes (`make typecheck`)
- [ ] Linting passes (`make lint`)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped in `pyproject.toml`
- [ ] Migration files reviewed
- [ ] Breaking changes documented

### Release

- [ ] Create release branch: `release/vX.Y.Z`
- [ ] Final testing on staging environment
- [ ] Create Git tag: `vX.Y.Z`
- [ ] Build and push Docker image
- [ ] Deploy to production
- [ ] Verify health checks
- [ ] Monitor error rates

### Post-Release

- [ ] Merge release branch to main
- [ ] Create GitHub release with notes
- [ ] Announce release (if applicable)
- [ ] Monitor for 24-48 hours
- [ ] Update documentation site

## Branching Strategy

```
main (production)
  │
  ├── develop (integration)
  │     │
  │     ├── feature/xyz
  │     └── feature/abc
  │
  └── release/vX.Y.Z (release candidate)
        │
        └── hotfix/issue-123 (if needed)
```

### Branch Types

| Branch | Purpose | Merges To |
|--------|---------|-----------|
| `main` | Production code | - |
| `develop` | Integration branch | `main` via release |
| `feature/*` | New features | `develop` |
| `release/*` | Release preparation | `main` and `develop` |
| `hotfix/*` | Production fixes | `main` and `develop` |

## Changelog Management

### Format

Follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/):

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- New features

### Changed
- Changes to existing features

### Deprecated
- Features to be removed

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Security patches
```

### Guidelines

1. Write entries for users, not developers
2. Group related changes
3. Link to issues/PRs where applicable
4. Include migration notes for breaking changes

## Version Bumping

### Using Python

```bash
# Update version in pyproject.toml
# Current: version = "0.1.0"

# For patch release
sed -i 's/version = "0.1.0"/version = "0.1.1"/' pyproject.toml

# Or manually edit pyproject.toml
```

### Git Tags

```bash
# Create annotated tag
git tag -a v1.0.0 -m "Release version 1.0.0"

# Push tag
git push origin v1.0.0

# List tags
git tag -l "v*"
```

## Deployment

### Staging Deployment

```bash
# Build and deploy to staging
make docker-build
docker push registry/django-finance:staging

# Or use CI/CD
git push origin release/v1.0.0
```

### Production Deployment

```bash
# After staging verification
docker tag registry/django-finance:staging registry/django-finance:v1.0.0
docker tag registry/django-finance:staging registry/django-finance:latest
docker push registry/django-finance:v1.0.0
docker push registry/django-finance:latest

# Deploy
kubectl set image deployment/django-finance app=registry/django-finance:v1.0.0
```

### Rollback

```bash
# Quick rollback to previous version
kubectl rollout undo deployment/django-finance

# Rollback to specific version
kubectl rollout undo deployment/django-finance --to-revision=2
```

## Hotfix Process

For critical production issues:

1. **Identify**: Confirm the issue in production
2. **Branch**: Create `hotfix/issue-XXX` from `main`
3. **Fix**: Implement minimal fix
4. **Test**: Verify fix resolves issue
5. **Release**: Follow expedited release process
6. **Merge**: Merge to both `main` and `develop`

```bash
# Create hotfix branch
git checkout main
git checkout -b hotfix/critical-bug

# Make fix, commit
git add .
git commit -m "fix: resolve critical authentication bypass"

# Merge to main
git checkout main
git merge hotfix/critical-bug
git tag -a v1.0.1 -m "Hotfix: critical authentication bypass"
git push origin main --tags

# Merge to develop
git checkout develop
git merge hotfix/critical-bug
git push origin develop

# Delete hotfix branch
git branch -d hotfix/critical-bug
```

## Release Communication

### Internal

- Slack notification to #engineering
- Email to stakeholders for major releases

### External (if applicable)

- Status page update
- Release notes on GitHub
- Blog post for major features
- Email to subscribers

## Automation

### GitHub Actions Release Workflow

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run tests
        run: make test

      - name: Build Docker image
        run: docker build -t django-finance:${{ github.ref_name }} .

      - name: Push to registry
        run: |
          docker push registry/django-finance:${{ github.ref_name }}
          docker push registry/django-finance:latest

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          generate_release_notes: true
```

## Emergency Procedures

### Security Vulnerability

1. **Do not disclose publicly**
2. Assess severity (CVSS score)
3. Develop fix in private branch
4. Prepare patch release
5. Deploy immediately
6. Notify affected users (if applicable)
7. Public disclosure after fix deployed

### Data Incident

1. Activate incident response team
2. Assess scope of impact
3. Contain the incident
4. Preserve evidence
5. Notify legal/compliance
6. User notification (per requirements)
7. Post-incident review

## Appendix

### Version History

| Version | Date | Notes |
|---------|------|-------|
| 0.1.0 | TBD | Initial release |

### Release Contacts

| Role | Contact |
|------|---------|
| Release Manager | TBD |
| Engineering Lead | TBD |
| Security | TBD |
