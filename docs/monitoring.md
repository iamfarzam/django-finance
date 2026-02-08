# Monitoring Configuration

## Overview

This document describes the monitoring setup for Django Finance in production.

## Health Endpoints

### Basic Health Check

**Endpoint**: `GET /health/`

Returns basic service health status.

```json
{
  "status": "healthy"
}
```

### Readiness Check

**Endpoint**: `GET /health/ready/`

Returns detailed readiness status with dependency checks.

```json
{
  "status": "ready",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "celery": "ok"
  }
}
```

## Prometheus Metrics

### Application Metrics

Recommended metrics to expose via `django-prometheus` or custom middleware:

```python
# Request metrics
http_requests_total{method, endpoint, status}
http_request_duration_seconds{method, endpoint}
http_request_size_bytes{method, endpoint}
http_response_size_bytes{method, endpoint}

# Database metrics
django_db_query_duration_seconds{query_type}
django_db_connections_active
django_db_connections_max

# Cache metrics
django_cache_hits_total
django_cache_misses_total
django_cache_get_duration_seconds

# Celery metrics
celery_tasks_total{task, status}
celery_task_duration_seconds{task}
celery_queue_size{queue}
```

### System Metrics

Collected via node_exporter or container metrics:

```
# CPU
node_cpu_seconds_total
process_cpu_seconds_total

# Memory
node_memory_MemTotal_bytes
node_memory_MemAvailable_bytes
process_resident_memory_bytes

# Disk
node_filesystem_size_bytes
node_filesystem_avail_bytes

# Network
node_network_receive_bytes_total
node_network_transmit_bytes_total
```

## Grafana Dashboards

### Application Dashboard

Key panels:
- Request rate (RPS)
- Error rate (%)
- Latency percentiles (p50, p95, p99)
- Active users
- Top endpoints by traffic

### Database Dashboard

Key panels:
- Query rate
- Query latency
- Active connections
- Connection pool usage
- Slow queries

### Infrastructure Dashboard

Key panels:
- CPU usage per instance
- Memory usage per instance
- Disk I/O
- Network traffic
- Container restarts

## Alerting Rules

### Critical Alerts (P1)

```yaml
# Service down
- alert: ServiceDown
  expr: up{job="django-finance"} == 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Django Finance is down"

# High error rate
- alert: HighErrorRate
  expr: |
    sum(rate(http_requests_total{status=~"5.."}[5m])) /
    sum(rate(http_requests_total[5m])) > 0.01
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Error rate above 1%"

# Database down
- alert: DatabaseDown
  expr: pg_up == 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "PostgreSQL is down"
```

### Warning Alerts (P2)

```yaml
# High latency
- alert: HighLatency
  expr: |
    histogram_quantile(0.95,
      sum(rate(http_request_duration_seconds_bucket[5m])) by (le)
    ) > 1
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "p95 latency above 1 second"

# High CPU
- alert: HighCPU
  expr: |
    100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
  for: 15m
  labels:
    severity: warning
  annotations:
    summary: "CPU usage above 80%"

# High memory
- alert: HighMemory
  expr: |
    (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100 > 85
  for: 15m
  labels:
    severity: warning
  annotations:
    summary: "Memory usage above 85%"

# Celery queue backlog
- alert: CeleryQueueBacklog
  expr: celery_queue_size > 100
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "Celery queue has over 100 pending tasks"
```

### Informational Alerts (P3/P4)

```yaml
# High disk usage
- alert: HighDiskUsage
  expr: |
    (1 - node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100 > 80
  for: 30m
  labels:
    severity: info
  annotations:
    summary: "Disk usage above 80%"

# Certificate expiry
- alert: CertificateExpiringSoon
  expr: probe_ssl_earliest_cert_expiry - time() < 86400 * 30
  for: 1h
  labels:
    severity: info
  annotations:
    summary: "SSL certificate expires in less than 30 days"
```

## Log Aggregation

### Log Format

Production uses JSON structured logging:

```json
{
  "timestamp": "2026-02-08T12:00:00.000Z",
  "level": "INFO",
  "logger": "django.request",
  "message": "GET /api/v1/dashboard/ 200",
  "correlation_id": "abc123",
  "user_id": "user-uuid",
  "method": "GET",
  "path": "/api/v1/dashboard/",
  "status_code": 200,
  "duration_ms": 45
}
```

### Log Queries

Common queries for investigation:

```
# All errors in last hour
level:ERROR AND @timestamp:[now-1h TO now]

# Slow requests (>1s)
duration_ms:>1000

# Specific user activity
user_id:"user-uuid"

# Failed logins
logger:"django.security" AND message:"login failed"

# Database errors
logger:"django.db.backends" AND level:ERROR
```

## Sentry Configuration

### Error Tracking

```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration

sentry_sdk.init(
    dsn="https://xxx@sentry.io/yyy",
    integrations=[
        DjangoIntegration(transaction_style="url"),
        CeleryIntegration(monitor_beat_tasks=True),
        RedisIntegration(),
    ],
    traces_sample_rate=0.1,
    profiles_sample_rate=0.1,
    environment="production",
)
```

### Performance Monitoring

Enable Sentry Performance to track:
- Transaction traces
- Database query performance
- External HTTP calls
- Celery task performance

## Uptime Monitoring

### External Monitoring

Configure external monitoring (e.g., Pingdom, UptimeRobot) for:

| Check | URL | Interval | Timeout |
|-------|-----|----------|---------|
| Health | `/health/` | 1 min | 10s |
| API | `/api/v1/dashboard/` | 5 min | 30s |
| Web | `/` | 5 min | 30s |

### Status Page

Consider using a status page service to communicate:
- Current system status
- Planned maintenance
- Incident updates

## Runbook Integration

Link monitoring alerts to runbook procedures:

| Alert | Runbook Section |
|-------|-----------------|
| ServiceDown | Incident Response |
| HighErrorRate | Common Issues > High Error Rate |
| DatabaseDown | Disaster Recovery |
| HighLatency | Common Issues > High Latency |
| CeleryQueueBacklog | Common Issues |

## Retention Policies

| Data Type | Retention |
|-----------|-----------|
| Metrics (raw) | 15 days |
| Metrics (5m avg) | 90 days |
| Metrics (1h avg) | 1 year |
| Logs | 30 days |
| Traces | 7 days |
| Error events | 90 days |
