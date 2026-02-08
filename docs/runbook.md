# Production Runbook

## Overview

This runbook provides operational procedures for Django Finance in production.

## Service Level Objectives (SLOs)

### Availability

| Metric | Target | Measurement |
|--------|--------|-------------|
| Uptime | 99.9% | Monthly |
| Health check success | 99.99% | Continuous |
| API availability | 99.9% | Monthly |

### Latency

| Endpoint Type | p50 | p95 | p99 |
|---------------|-----|-----|-----|
| Health checks | 50ms | 100ms | 200ms |
| API read | 200ms | 500ms | 1s |
| API write | 500ms | 1s | 2s |
| Dashboard | 300ms | 700ms | 1.5s |
| Reports | 1s | 2s | 5s |

### Error Rate

| Metric | Target |
|--------|--------|
| 5xx errors | < 0.1% |
| 4xx errors | < 1% |
| Failed transactions | < 0.01% |

### Throughput

| Scenario | Target RPS |
|----------|-----------|
| Sustained | 100 |
| Peak | 500 |
| Burst (1 min) | 1000 |

---

## Architecture Overview

```
                    ┌─────────────────┐
                    │   Load Balancer │
                    │   (HTTPS/443)   │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
        ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
        │  Django   │  │  Django   │  │  Django   │
        │  (Daphne) │  │  (Daphne) │  │  (Daphne) │
        └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
              │              │              │
              └──────────────┼──────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
   ┌─────▼─────┐       ┌─────▼─────┐       ┌─────▼─────┐
   │ PostgreSQL│       │   Redis   │       │  Celery   │
   │ (Primary) │       │  Cluster  │       │  Workers  │
   └───────────┘       └───────────┘       └───────────┘
```

---

## Health Checks

### Endpoints

| Endpoint | Purpose | Expected Response |
|----------|---------|-------------------|
| `/health/` | Basic health | `{"status": "healthy"}` |
| `/health/ready/` | Readiness | `{"status": "ready", "checks": {...}}` |

### Health Check Script

```bash
#!/bin/bash
# health_check.sh

HEALTH_URL="${1:-http://localhost:8000/health/}"
TIMEOUT=5

response=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT "$HEALTH_URL")

if [ "$response" = "200" ]; then
    echo "OK"
    exit 0
else
    echo "FAILED (HTTP $response)"
    exit 1
fi
```

---

## Startup Procedures

### Pre-flight Checks

```bash
# 1. Verify database connectivity
python manage.py dbshell -c "SELECT 1;"

# 2. Verify Redis connectivity
python manage.py shell -c "from django.core.cache import cache; cache.set('test', 1); print(cache.get('test'))"

# 3. Run migrations check
python manage.py migrate --check

# 4. Collect static files
python manage.py collectstatic --noinput
```

### Start Application

```bash
# Start Daphne (ASGI server)
daphne -b 0.0.0.0 -p 8000 config.asgi:application

# Start Celery worker
celery -A config worker -l INFO --concurrency=4

# Start Celery beat
celery -A config beat -l INFO
```

### Verify Startup

```bash
# Check health endpoint
curl -f http://localhost:8000/health/

# Check readiness
curl -f http://localhost:8000/health/ready/

# Check logs for errors
tail -f /var/log/django-finance/app.log | grep -i error
```

---

## Shutdown Procedures

### Graceful Shutdown

```bash
# 1. Stop accepting new connections (load balancer)
# Remove instance from load balancer target group

# 2. Wait for in-flight requests (30 seconds)
sleep 30

# 3. Stop Celery beat (no new tasks)
celery -A config control shutdown_beat

# 4. Wait for Celery tasks to complete
celery -A config control shutdown --timeout=60

# 5. Stop application server
kill -TERM $(pgrep daphne)
```

### Emergency Shutdown

```bash
# Immediate stop (may lose in-flight requests)
pkill -9 daphne
pkill -9 celery
```

---

## Deployment Procedures

### Blue-Green Deployment

1. **Prepare new environment (Green)**
   ```bash
   # Deploy new version to green environment
   ./deploy.sh green

   # Run migrations on green
   python manage.py migrate

   # Warm up green
   curl http://green:8000/health/
   ```

2. **Switch traffic**
   ```bash
   # Update load balancer to point to green
   aws elb modify-listener --target-group green-tg
   ```

3. **Verify**
   ```bash
   # Monitor for 5 minutes
   watch -n 5 'curl -s http://app/health/'
   ```

4. **Rollback if needed**
   ```bash
   # Switch back to blue
   aws elb modify-listener --target-group blue-tg
   ```

### Rolling Deployment

```bash
# Deploy to one instance at a time
for instance in instance1 instance2 instance3; do
    # Remove from load balancer
    aws elb deregister-targets --target-group-arn $TG_ARN --targets Id=$instance

    # Wait for drain
    sleep 30

    # Deploy
    ssh $instance "cd /app && git pull && pip install -r requirements.txt"
    ssh $instance "systemctl restart django-finance"

    # Health check
    ssh $instance "curl -f http://localhost:8000/health/"

    # Add back to load balancer
    aws elb register-targets --target-group-arn $TG_ARN --targets Id=$instance

    # Wait for healthy
    sleep 30
done
```

---

## Rollback Procedures

### Application Rollback

```bash
# 1. Identify previous version
git log --oneline -5

# 2. Checkout previous version
git checkout <previous-commit>

# 3. Reinstall dependencies
pip install -r requirements.txt

# 4. Restart application
systemctl restart django-finance

# 5. Verify
curl http://localhost:8000/health/
```

### Database Rollback

```bash
# 1. List migration history
python manage.py showmigrations

# 2. Rollback specific migration
python manage.py migrate <app_name> <migration_name>

# Example: Rollback finance to 0005
python manage.py migrate finance 0005
```

### Full Rollback (Restore from Backup)

```bash
# 1. Stop application
systemctl stop django-finance

# 2. Restore database
pg_restore -h $DB_HOST -U $DB_USER -d django_finance backup.dump

# 3. Checkout matching code version
git checkout <matching-commit>

# 4. Restart application
systemctl restart django-finance
```

---

## Backup Procedures

### Database Backup

```bash
# Daily automated backup
pg_dump -h $DB_HOST -U $DB_USER -Fc django_finance > backup_$(date +%Y%m%d).dump

# Upload to S3
aws s3 cp backup_$(date +%Y%m%d).dump s3://backups/django-finance/

# Verify backup
pg_restore --list backup_$(date +%Y%m%d).dump
```

### Backup Schedule

| Type | Frequency | Retention |
|------|-----------|-----------|
| Full backup | Daily | 30 days |
| Transaction log | Continuous | 7 days |
| Weekly snapshot | Weekly | 90 days |
| Monthly archive | Monthly | 1 year |

### Restore Test (Monthly)

```bash
# 1. Create test database
createdb -h $DB_HOST -U $DB_USER django_finance_restore_test

# 2. Restore backup
pg_restore -h $DB_HOST -U $DB_USER -d django_finance_restore_test latest_backup.dump

# 3. Verify data
psql -h $DB_HOST -U $DB_USER -d django_finance_restore_test -c "SELECT COUNT(*) FROM accounts_user;"

# 4. Cleanup
dropdb -h $DB_HOST -U $DB_USER django_finance_restore_test
```

---

## Incident Response

### Severity Levels

| Level | Description | Response Time | Examples |
|-------|-------------|---------------|----------|
| P1 | Service down | 15 min | Complete outage |
| P2 | Degraded | 1 hour | High error rate, slow responses |
| P3 | Minor issue | 4 hours | Single feature broken |
| P4 | Low impact | 24 hours | Cosmetic issues |

### Incident Workflow

1. **Detect**: Alert triggered or user report
2. **Acknowledge**: Assign owner, update status page
3. **Investigate**: Check logs, metrics, recent changes
4. **Mitigate**: Apply immediate fix or rollback
5. **Resolve**: Permanent fix deployed
6. **Review**: Post-incident review within 48 hours

### Common Issues

#### High Error Rate

```bash
# Check recent errors
tail -1000 /var/log/django-finance/app.log | grep ERROR

# Check database connections
psql -c "SELECT count(*) FROM pg_stat_activity WHERE datname='django_finance';"

# Check Redis
redis-cli ping
redis-cli info memory
```

#### High Latency

```bash
# Check slow queries
psql -c "SELECT query, calls, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Check Celery queue
celery -A config inspect active
celery -A config inspect reserved

# Check CPU/memory
top -b -n 1 | head -20
```

#### Database Connection Exhausted

```bash
# Check active connections
psql -c "SELECT usename, count(*) FROM pg_stat_activity GROUP BY usename;"

# Kill idle connections
psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND query_start < now() - interval '1 hour';"

# Restart application (will reset connection pool)
systemctl restart django-finance
```

---

## Disaster Recovery

### Recovery Point Objective (RPO)

- **Target**: 1 hour
- **Method**: Continuous WAL archiving + hourly backups

### Recovery Time Objective (RTO)

- **Target**: 4 hours
- **Method**: Automated recovery with Infrastructure as Code

### Disaster Scenarios

#### Single Instance Failure

1. Load balancer detects failure via health check
2. Traffic automatically routed to healthy instances
3. Auto-scaling launches replacement instance
4. **Recovery time**: < 5 minutes

#### Database Failure

1. Failover to standby (if configured)
2. Or restore from latest backup
3. Point-in-time recovery if needed
4. **Recovery time**: < 1 hour

#### Full Region Failure

1. DNS failover to DR region
2. Promote standby database
3. Start application in DR region
4. **Recovery time**: < 4 hours

### DR Test (Quarterly)

1. Schedule maintenance window
2. Simulate primary region failure
3. Execute failover procedure
4. Verify functionality in DR region
5. Failback to primary
6. Document findings

---

## Monitoring Dashboards

### Key Metrics

| Metric | Warning | Critical |
|--------|---------|----------|
| Error rate (5xx) | > 0.5% | > 1% |
| Latency p99 | > 2s | > 5s |
| CPU usage | > 70% | > 90% |
| Memory usage | > 80% | > 95% |
| Disk usage | > 80% | > 90% |
| DB connections | > 80% | > 95% |
| Celery queue size | > 100 | > 500 |

### Alerting

```yaml
# Example Prometheus alerting rules
groups:
  - name: django-finance
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: High error rate detected

      - alert: HighLatency
        expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: High latency detected
```

---

## Contact Information

| Role | Contact | Escalation |
|------|---------|------------|
| On-call Engineer | PagerDuty | Automatic |
| Engineering Lead | Slack #eng-leads | After 30 min |
| VP Engineering | Phone | P1 > 1 hour |

---

## Appendix

### Useful Commands

```bash
# View application logs
journalctl -u django-finance -f

# View Celery logs
journalctl -u celery-worker -f

# Database shell
python manage.py dbshell

# Django shell
python manage.py shell_plus

# Check migrations
python manage.py showmigrations

# Clear cache
python manage.py shell -c "from django.core.cache import cache; cache.clear()"
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `REDIS_URL` | Redis connection string | Yes |
| `SECRET_KEY` | Django secret key | Yes |
| `ALLOWED_HOSTS` | Comma-separated hosts | Yes |
| `SENTRY_DSN` | Sentry error tracking | No |
| `DEBUG` | Debug mode (never true in prod) | No |
