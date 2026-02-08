# Performance Testing Guide

## Overview

This document describes the performance testing strategy, tools, and baselines for Django Finance.

## Tools

### Locust (Load Testing)

We use [Locust](https://locust.io/) for load testing. It provides:
- Python-based test scenarios
- Real-time web UI for monitoring
- Distributed testing support
- CI/CD integration via headless mode

### Installation

```bash
pip install locust
```

## Running Load Tests

### Interactive Mode (Development)

```bash
# Start Locust with web UI
locust -f tests/performance/locustfile.py --host=http://localhost:8000

# Open http://localhost:8089 in browser
# Configure users and spawn rate
# Start the test
```

### Headless Mode (CI/CD)

```bash
# Run with 100 users, spawn 10/sec, for 5 minutes
locust -f tests/performance/locustfile.py \
    --headless \
    -u 100 \
    -r 10 \
    -t 5m \
    --host=http://localhost:8000 \
    --csv=results/load_test
```

### Distributed Mode

```bash
# Master node
locust -f tests/performance/locustfile.py --master --host=http://localhost:8000

# Worker nodes (run on multiple machines)
locust -f tests/performance/locustfile.py --worker --master-host=<master-ip>
```

## Test Scenarios

### AuthenticatedAPIUser

Simulates authenticated users interacting with the API:

| Endpoint | Weight | Description |
|----------|--------|-------------|
| GET /api/v1/dashboard/ | 20 | Dashboard (most accessed) |
| GET /api/v1/finance/accounts/ | 10 | List accounts |
| GET /api/v1/finance/transactions/ | 8 | List transactions |
| GET /api/v1/finance/accounts/[id]/ | 5 | Account detail |
| GET /api/v1/finance/reports/net-worth/ | 5 | Net worth report |
| GET /api/v1/social/contacts/ | 5 | List contacts |
| GET /api/v1/social/peer-debts/ | 3 | List debts |
| POST /api/v1/finance/transactions/ | 3 | Create transaction |
| POST /api/v1/finance/accounts/ | 2 | Create account |
| POST /api/v1/social/contacts/ | 1 | Create contact |

### WebUIUser

Simulates users browsing the web interface:

| Page | Weight | Description |
|------|--------|-------------|
| / | 10 | Dashboard |
| /accounts/login/ | 5 | Login page |
| /accounts/ | 3 | Accounts list |
| /transactions/ | 3 | Transactions list |
| /contacts/ | 2 | Contacts list |
| /health/ | 1 | Health check |

## Performance Baselines

### Response Time Targets

| Endpoint Type | p50 | p95 | p99 |
|---------------|-----|-----|-----|
| Health checks | < 50ms | < 100ms | < 200ms |
| Read endpoints | < 200ms | < 500ms | < 1s |
| Write endpoints | < 500ms | < 1s | < 2s |
| Reports | < 1s | < 2s | < 5s |

### Throughput Targets

| Scenario | Target RPS | Notes |
|----------|-----------|-------|
| Normal load | 100 | Typical production traffic |
| Peak load | 500 | 5x normal traffic |
| Stress test | 1000 | Breaking point analysis |

### Error Rate Targets

| Metric | Target |
|--------|--------|
| Error rate (4xx) | < 1% |
| Error rate (5xx) | < 0.1% |
| Timeout rate | < 0.5% |

## Database Optimization

### Query Optimization

1. **Use select_related/prefetch_related**: Avoid N+1 queries
2. **Add database indexes**: On frequently filtered fields
3. **Use pagination**: Cursor-based pagination for large datasets
4. **Cache expensive queries**: Use Django cache framework

### Connection Pooling

Production settings include:
```python
DATABASES["default"]["CONN_MAX_AGE"] = 600  # 10 minutes
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True
```

## Caching Strategy

### Cache Layers

1. **Application Cache (Redis)**
   - Session storage
   - Rate limiting counters
   - Subscription context (TTL: 5 minutes)

2. **Database Query Cache**
   - Expensive aggregations
   - Report generation

3. **HTTP Cache Headers**
   - Static assets (1 year)
   - API responses (vary by user)

### Cache Configuration

```python
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://localhost:6379/0",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "MAX_CONNECTIONS": 50,
        },
        "KEY_PREFIX": "dj_finance",
    }
}
```

## Monitoring During Tests

### Metrics to Watch

1. **Response times** (p50, p95, p99)
2. **Request rate** (RPS)
3. **Error rate** (4xx, 5xx)
4. **CPU usage** (application server, database)
5. **Memory usage** (application server, Redis)
6. **Database connections** (active, waiting)
7. **Redis memory** and hit rate

### Grafana Dashboards

Create dashboards for:
- API endpoint latency
- Database query performance
- Cache hit/miss rates
- Celery task queues

## CI/CD Integration

### GitHub Actions Example

```yaml
performance-test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4

    - name: Start services
      run: docker-compose up -d

    - name: Run load test
      run: |
        pip install locust
        locust -f tests/performance/locustfile.py \
          --headless \
          -u 50 \
          -r 5 \
          -t 2m \
          --host=http://localhost:8000 \
          --csv=results/load_test \
          --exit-code-on-error 1

    - name: Upload results
      uses: actions/upload-artifact@v4
      with:
        name: load-test-results
        path: results/
```

## Troubleshooting

### High Response Times

1. Check database query performance (Django Debug Toolbar)
2. Review slow query logs
3. Check for missing indexes
4. Verify cache is being used

### High Error Rates

1. Check application logs
2. Review rate limiting configuration
3. Verify database connection limits
4. Check Redis connection pool

### Memory Issues

1. Monitor for memory leaks
2. Check Celery task queue size
3. Review cache eviction policies
4. Consider horizontal scaling
