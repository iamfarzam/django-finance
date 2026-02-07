# Django Finance

Finance management SaaS (B2C) platform for tracking cash inflow/outflow, loans, assets, liabilities, and related records.

## Tech Stack

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.12+ | Runtime |
| Django | 5.2 LTS | Web framework |
| Django REST Framework | 3.16+ | REST API |
| Django Channels | 4.3+ | WebSocket |
| Celery | 5.6+ | Background tasks |
| PostgreSQL | 16+ | Database |
| Redis | 7.2+ | Cache/Broker |

## Baseline Documentation

| Document | Purpose |
|----------|---------|
| [`TECH_STACK.md`](docs/TECH_STACK.md) | Version matrix and dependencies |
| [`ENGINEERING_BASELINE.md`](docs/ENGINEERING_BASELINE.md) | Engineering standards and architecture |
| [`PRODUCT_BASELINE.md`](docs/PRODUCT_BASELINE.md) | Product strategy and B2C SaaS requirements |
| [`conventions.md`](docs/conventions.md) | Naming and coding conventions |
| [`security.md`](docs/security.md) | Security policies and compliance |
| [`PLAN.md`](docs/PLAN.md) | Project phases and milestones |
| [`CHANGELOG.md`](docs/CHANGELOG.md) | Change tracking |

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Start services
make up

# Run migrations
make migrate

# Start development server
make runserver
```

## Project Status

**Phase 1: Architecture Baseline** - Complete

Baseline documentation established: 2026-02-07

## License

MIT. See [`LICENSE`](LICENSE).
