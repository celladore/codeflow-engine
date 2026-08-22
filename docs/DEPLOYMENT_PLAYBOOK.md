# Deployment Playbook
## CodeFlow Engine - Production Deployment Guide

**Version:** 1.0.0  
**Last Updated:** 2025-11-22  
**Status:** Production-Ready

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Setup](#environment-setup)
3. [Database Deployment](#database-deployment)
4. [Application Deployment](#application-deployment)
5. [Service Configuration](#service-configuration)
6. [Health Checks & Validation](#health-checks--validation)
7. [Rollback Procedures](#rollback-procedures)
8. [Post-Deployment](#post-deployment)
9. [Monitoring Setup](#monitoring-setup)
10. [Disaster Recovery](#disaster-recovery)

---

## Pre-Deployment Checklist

### Documentation Review
- [ ] Review all recent code changes and PR descriptions
- [ ] Check CHANGELOG.md for breaking changes
- [ ] Review security advisories and known issues
- [ ] Verify all tests pass in CI/CD pipeline

### Infrastructure Preparation
- [ ] Verify sufficient resources (CPU, memory, disk space)
- [ ] Ensure database backup is recent (< 24 hours)
- [ ] Check network connectivity and firewall rules
- [ ] Verify SSL/TLS certificates are valid
- [ ] Confirm DNS records are correct

### Security Verification
- [ ] Rotate secrets and API keys if needed
- [ ] Verify GitHub token scopes and permissions
- [ ] Check database user permissions
- [ ] Review security scanning results (CodeQL, SAST)
- [ ] Ensure all dependencies are up to date

### Team Coordination
- [ ] Schedule maintenance window (if required)
- [ ] Notify stakeholders of deployment timeline
- [ ] Ensure rollback team is available
- [ ] Verify on-call engineer availability
- [ ] Prepare communication templates

---

## Environment Setup

### 1. Environment Variables

Create a `.env.production` file with the following configuration:

```bash
# Application
APP_ENV=production
APP_DEBUG=false
LOG_LEVEL=INFO
PORT=8000
DASHBOARD_PORT=8080

# Database (PostgreSQL)
DATABASE_URL=postgresql://user:password@localhost:5432/codeflow_prod
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# Redis (Caching & Queues)
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50

# GitHub Integration
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GITHUB_APP_ID=123456
GITHUB_PRIVATE_KEY_PATH=/path/to/github-app-private-key.pem
GITHUB_WEBHOOK_SECRET=your_webhook_secret_here

# AI Providers (Configure at least one)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
MISTRAL_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Integrations (Optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/xxxxxxxxxxxxxxxxxxxx
LINEAR_API_KEY=lin_api_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Security
SECRET_KEY=generate-a-secure-random-key-here
JWT_SECRET=generate-another-secure-random-key
ALLOWED_HOSTS=codeflow.example.com,api.codeflow.example.com
CORS_ORIGINS=https://codeflow.example.com

# Performance
WORKER_PROCESSES=4
WORKER_THREADS=2
MAX_CONCURRENT_WORKFLOWS=50
REQUEST_TIMEOUT=300

# Monitoring (Optional)
SENTRY_DSN=https://xxxxxxxxxxxx@sentry.io/1234567
PROMETHEUS_PORT=9090
```

### 2. System Requirements

**Minimum Requirements:**
- CPU: 2 cores
- RAM: 4 GB
- Disk: 20 GB SSD
- Network: 100 Mbps

**Recommended (Production):**
- CPU: 4-8 cores
- RAM: 16 GB
- Disk: 100 GB SSD (with backup)
- Network: 1 Gbps

### 3. Dependencies Installation

```bash
# System packages (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y \
    python3.12 \
    python3.12-venv \
    postgresql-client \
    redis-tools \
    nginx \
    supervisor

# Python virtual environment
python3.12 -m venv /opt/CodeFlow/venv
source /opt/CodeFlow/venv/bin/activate

# Python dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt --no-cache-dir

# Verify installation
python -m codeflow.version
python -m codeflow.health_check
```

---

## Database Deployment

### 1. Database Preparation

```bash
# Connect to PostgreSQL
psql -h localhost -U postgres

# Create database and user
CREATE DATABASE codeflow_prod;
CREATE USER codeflow_user WITH ENCRYPTED PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE codeflow_prod TO codeflow_user;

# Enable required extensions
\c codeflow_prod
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search
CREATE EXTENSION IF NOT EXISTS "btree_gin"; -- For index optimization
```

### 2. Database Migration

```bash
# Export connection string
export DATABASE_URL=postgresql://codeflow_user:secure_password@localhost:5432/codeflow_prod

# Run migrations
alembic upgrade head

# Verify migration status
alembic current
alembic history

# Verify table creation
psql $DATABASE_URL -c "\dt"
```

### 3. Database Optimization

```bash
# Apply database optimizations (see DATABASE_OPTIMIZATION_GUIDE.md)
psql $DATABASE_URL -f scripts/db_optimizations.sql

# Verify indexes
psql $DATABASE_URL -c "
SELECT 
    tablename, 
    indexname, 
    indexdef 
FROM pg_indexes 
WHERE schemaname = 'public' 
ORDER BY tablename, indexname;
"

# Analyze tables for query planner
psql $DATABASE_URL -c "ANALYZE;"
```

---

## Application Deployment

### 1. Code Deployment

```bash
# Clone repository (or pull latest)
cd /opt/CodeFlow
git clone https://github.com/your-org/codeflow-engine.git .
# OR
git pull origin main

# Checkout specific version/tag
git checkout v1.0.1

# Verify code integrity
git verify-tag v1.0.1
```

### 2. Build Application

```bash
# Activate virtual environment
source /opt/CodeFlow/venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests (optional but recommended)
pytest tests/ -v --tb=short

# Build frontend (if applicable)
cd codeflow-desktop
pnpm install
pnpm run build
cd ..
```

### 3. Configuration Deployment

```bash
# Copy configuration files
cp .env.production /opt/CodeFlow/.env
cp config/production.yaml /opt/CodeFlow/config/config.yaml

# Set proper permissions
chmod 600 /opt/CodeFlow/.env
chmod 644 /opt/CodeFlow/config/config.yaml

# Verify configuration
python -c "from codeflow_engine.config import load_config; print(load_config())"
```

---

## Service Configuration

### 1. Systemd Service (Main API)

Create `/etc/systemd/system/codeflow-api.service`:

```ini
[Unit]
Description=CodeFlow Engine API
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=notify
User=CodeFlow
Group=CodeFlow
WorkingDirectory=/opt/CodeFlow
Environment="PATH=/opt/CodeFlow/venv/bin"
EnvironmentFile=/opt/CodeFlow/.env

ExecStart=/opt/CodeFlow/venv/bin/gunicorn \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 300 \
    --access-logfile /var/log/CodeFlow/access.log \
    --error-logfile /var/log/CodeFlow/error.log \
    --log-level info \
    codeflow.main:app

ExecReload=/bin/kill -s HUP $MAINPID
ExecStop=/bin/kill -s TERM $MAINPID

Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/log/CodeFlow /opt/CodeFlow/data

[Install]
WantedBy=multi-user.target
```

### 2. Systemd Service (Dashboard)

Create `/etc/systemd/system/codeflow-dashboard.service`:

```ini
[Unit]
Description=CodeFlow Engine Dashboard
After=network.target codeflow-api.service
Wants=codeflow-api.service

[Service]
Type=simple
User=CodeFlow
Group=CodeFlow
WorkingDirectory=/opt/CodeFlow
Environment="PATH=/opt/CodeFlow/venv/bin"
EnvironmentFile=/opt/CodeFlow/.env

ExecStart=/opt/CodeFlow/venv/bin/python -m codeflow.dashboard.server

Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/log/CodeFlow /opt/CodeFlow/data

[Install]
WantedBy=multi-user.target
```

### 3. Nginx Configuration

Create `/etc/nginx/sites-available/CodeFlow`:

```nginx
upstream codeflow_api {
    server 127.0.0.1:8000 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

upstream codeflow_dashboard {
    server 127.0.0.1:8080 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name codeflow.example.com;
    return 301 https://$server_name$request_uri;
}

# Main HTTPS server
server {
    listen 443 ssl http2;
    server_name codeflow.example.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/codeflow.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/codeflow.example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # API Endpoints
    location /api/ {
        proxy_pass http://codeflow_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # Dashboard
    location / {
        proxy_pass http://codeflow_dashboard;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://codeflow_dashboard;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }

    # Static files (if any)
    location /static/ {
        alias /opt/CodeFlow/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Health check endpoint (bypass auth)
    location /health {
        proxy_pass http://codeflow_api/api/health;
        access_log off;
    }
}
```

### 4. Enable and Start Services

```bash
# Enable services
sudo systemctl enable codeflow-api.service
sudo systemctl enable codeflow-dashboard.service
sudo systemctl enable nginx

# Start services
sudo systemctl start codeflow-api.service
sudo systemctl start codeflow-dashboard.service
sudo systemctl restart nginx

# Check service status
sudo systemctl status codeflow-api.service
sudo systemctl status codeflow-dashboard.service
sudo systemctl status nginx

# View logs
sudo journalctl -u codeflow-api.service -f
sudo journalctl -u codeflow-dashboard.service -f
```

---

## Health Checks & Validation

### 1. Service Health Checks

```bash
# Check API health
curl -f http://localhost:8000/api/health || echo "API health check failed"

# Check dashboard health
curl -f http://localhost:8080/api/health || echo "Dashboard health check failed"

# Check database connectivity
psql $DATABASE_URL -c "SELECT 1;" || echo "Database connection failed"

# Check Redis connectivity
redis-cli -h localhost ping || echo "Redis connection failed"
```

### 2. Integration Tests

```bash
# Run integration tests against deployed environment
export codeflow_API_URL=https://codeflow.example.com
pytest tests/integration/ -v --tb=short

# Test workflow creation
curl -X POST https://codeflow.example.com/api/workflows/ \
    -H "Authorization: Bearer $GITHUB_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "test-workflow",
        "description": "Test deployment",
        "trigger": "manual"
    }'
```

### 3. Performance Validation

```bash
# Check response times
time curl -s https://codeflow.example.com/api/health > /dev/null

# Load test (using Apache Bench)
ab -n 1000 -c 10 https://codeflow.example.com/api/health

# Check database connection pool
psql $DATABASE_URL -c "
SELECT 
    count(*) as active_connections,
    max_conn - count(*) as available_connections
FROM pg_stat_activity, 
    (SELECT setting::int as max_conn FROM pg_settings WHERE name = 'max_connections') s
WHERE datname = 'codeflow_prod';
"
```

### 4. Security Validation

```bash
# Check SSL certificate
openssl s_client -connect codeflow.example.com:443 -servername codeflow.example.com < /dev/null

# Verify HTTPS redirect
curl -I http://codeflow.example.com | grep "301\|302"

# Check security headers
curl -I https://codeflow.example.com | grep -E "X-Frame-Options|X-Content-Type-Options|Strict-Transport-Security"

# Verify file permissions
ls -la /opt/CodeFlow/.env | grep "600"
```

---

## Rollback Procedures

### Emergency Rollback

If critical issues are detected post-deployment:

```bash
# 1. Stop services immediately
sudo systemctl stop codeflow-api.service
sudo systemctl stop codeflow-dashboard.service

# 2. Restore previous code version
cd /opt/CodeFlow
git checkout tags/v1.0.0  # Previous stable version

# 3. Restore database (if needed)
# WARNING: This will lose data since backup!
psql -h localhost -U postgres -c "DROP DATABASE codeflow_prod;"
psql -h localhost -U postgres -c "CREATE DATABASE codeflow_prod;"
pg_restore -d codeflow_prod /backups/codeflow_prod_pre_deployment.dump

# 4. Restart services
sudo systemctl start codeflow-api.service
sudo systemctl start codeflow-dashboard.service

# 5. Verify rollback
curl -f https://codeflow.example.com/api/health
```

### Gradual Rollback (Blue-Green)

If using blue-green deployment:

```bash
# 1. Route traffic back to blue (old) environment
# Update load balancer or nginx upstream

# 2. Monitor for stabilization
# Check metrics and logs

# 3. Keep green (new) environment for investigation
# Debug issues without customer impact
```

---

## Post-Deployment

### 1. Monitoring Verification

```bash
# Verify metrics are being collected
curl http://localhost:9090/metrics

# Check Sentry for errors
# Visit Sentry dashboard and verify error reporting

# Verify log aggregation
# Check your log aggregation service (e.g., ELK, DataDog)
```

### 2. Smoke Tests

```bash
# Create a test workflow
WORKFLOW_ID=$(curl -X POST https://codeflow.example.com/api/workflows/ \
    -H "Authorization: Bearer $GITHUB_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"name":"smoke-test","trigger":"manual"}' | jq -r '.workflow_id')

# Execute workflow
curl -X POST https://codeflow.example.com/api/workflows/$WORKFLOW_ID/execute \
    -H "Authorization: Bearer $GITHUB_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"context":{"test":true}}'

# Verify execution
curl https://codeflow.example.com/api/workflows/$WORKFLOW_ID \
    -H "Authorization: Bearer $GITHUB_TOKEN"
```

### 3. Documentation Updates

- [ ] Update deployment log with version and timestamp
- [ ] Document any manual configuration changes
- [ ] Update runbook with new procedures (if any)
- [ ] Notify team of successful deployment

### 4. Stakeholder Communication

```
Subject: CodeFlow Engine Deployment - v1.0.1 Complete

Team,

The deployment of CodeFlow Engine v1.0.1 to production has been completed successfully.

Deployment Details:
- Version: v1.0.1
- Deployment Time: 2025-11-22 18:00 UTC
- Downtime: None (rolling update)
- Status: All health checks passing

Key Changes:
- Security fixes (BUG-2, BUG-3, BUG-6, BUG-9)
- Database optimization
- API reference documentation
- Exception sanitization

Monitoring:
- Dashboard: https://codeflow.example.com
- Metrics: https://metrics.codeflow.example.com
- Logs: https://logs.codeflow.example.com

Please report any issues to the on-call team.

Regards,
DevOps Team
```

---

## Monitoring Setup

### 1. Application Metrics

Configure Prometheus scraping:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'codeflow-api'
    static_configs:
      - targets: ['localhost:9090']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### 2. Health Check Monitoring

Configure uptime monitoring (e.g., UptimeRobot, Pingdom):

- **Endpoint:** https://codeflow.example.com/api/health
- **Interval:** 1 minute
- **Timeout:** 10 seconds
- **Alert:** Email/SMS on failure

### 3. Log Aggregation

Configure log shipping to centralized logging:

```bash
# rsyslog or filebeat configuration
# Ship logs from /var/log/CodeFlow/* to ELK/Splunk/DataDog
```

### 4. Alert Configuration

Set up alerts for:
- API response time > 5s (warning), > 10s (critical)
- Error rate > 1% (warning), > 5% (critical)
- Database connection pool exhausted
- Disk usage > 80% (warning), > 90% (critical)
- Memory usage > 80% (warning), > 90% (critical)

---

## Disaster Recovery

### 1. Backup Strategy

**Database Backups:**
```bash
# Daily full backup
0 2 * * * pg_dump -Fc codeflow_prod > /backups/codeflow_prod_$(date +\%Y\%m\%d).dump

# Hourly incremental backup (using WAL archiving)
# Configure in postgresql.conf:
# archive_mode = on
# archive_command = 'cp %p /backups/wal/%f'
```

**Application Backups:**
```bash
# Backup configuration and data
0 3 * * * tar -czf /backups/codeflow_app_$(date +\%Y\%m\%d).tar.gz /opt/CodeFlow/.env /opt/CodeFlow/data
```

### 2. Recovery Procedures

**Database Recovery:**
```bash
# Full restore from backup
pg_restore -d codeflow_prod /backups/codeflow_prod_20251122.dump

# Point-in-time recovery (if WAL archiving enabled)
# 1. Restore base backup
# 2. Copy WAL files to pg_wal/
# 3. Configure recovery.conf with target time
# 4. Start PostgreSQL
```

**Application Recovery:**
```bash
# Restore application files
tar -xzf /backups/codeflow_app_20251122.tar.gz -C /opt/CodeFlow

# Restart services
sudo systemctl restart codeflow-api.service
sudo systemctl restart codeflow-dashboard.service
```

### 3. Backup Testing

Schedule monthly backup restoration tests:
```bash
# Test restoration in non-production environment
# Verify data integrity
# Document restoration time (RTO)
```

---

## Troubleshooting

### Common Deployment Issues

**1. Service Won't Start**
```bash
# Check service logs
sudo journalctl -u codeflow-api.service -n 50

# Check file permissions
ls -la /opt/CodeFlow/.env

# Verify dependencies
source /opt/CodeFlow/venv/bin/activate
pip check
```

**2. Database Migration Failure**
```bash
# Check current migration state
alembic current

# Manually apply failed migration
alembic upgrade +1

# Force revision (last resort)
alembic stamp head
```

**3. High Memory Usage**
```bash
# Check process memory
ps aux | grep CodeFlow | awk '{print $6}' | awk '{sum+=$1} END {print sum/1024 " MB"}'

# Restart services
sudo systemctl restart codeflow-api.service

# Adjust worker count in systemd service file
```

**4. Connection Pool Exhausted**
```bash
# Check active connections
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity WHERE datname = 'codeflow_prod';"

# Increase pool size in .env
DB_POOL_SIZE=30
DB_MAX_OVERFLOW=60

# Restart service
sudo systemctl restart codeflow-api.service
```

---

## Deployment Checklist Summary

### Pre-Deployment
- [ ] Code review and testing complete
- [ ] Database backup created
- [ ] Team notified
- [ ] Rollback plan prepared

### Deployment
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Services started successfully
- [ ] Nginx configuration updated

### Validation
- [ ] Health checks passing
- [ ] Integration tests passing
- [ ] Performance metrics acceptable
- [ ] Security validation complete

### Post-Deployment
- [ ] Monitoring configured
- [ ] Smoke tests passing
- [ ] Documentation updated
- [ ] Stakeholders notified

---

## Additional Resources

- **Troubleshooting Guide:** `docs/TROUBLESHOOTING.md`
- **Database Optimization:** `docs/DATABASE_OPTIMIZATION_GUIDE.md`
- **API Reference:** `docs/API_REFERENCE.md`
- **Security Best Practices:** `docs/security/SECURITY_BEST_PRACTICES.md`

---

## Contact & Support

**Deployment Issues:**
- On-call team: oncall@example.com
- Emergency hotline: +1-555-0100

**Documentation Issues:**
- Submit PR or issue on GitHub
- Email: devops@example.com

---

**Document Version:** 1.0.0  
**Last Review:** 2025-11-22  
**Next Review:** 2026-02-22
