# Analytics Service Deployment Guide

## Quick Start

### Prerequisites
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+
- Python 3.11 (for local development)
- Git

### Environment Variables

Create `.env` file:
```bash
# Database Configuration
DB_USER=railway_user
DB_PASSWORD=secure_password
DATABASE_URL=postgresql://railway_user:secure_password@postgres:5432/railway_os

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Service Configuration
ANALYTICS_SERVICE_URL=http://analytics-service:8084
ANALYTICS_PORT=8084
DEBUG_MODE=false
LOG_LEVEL=INFO

# API Gateway Configuration
API_GATEWAY_URL=http://api-gateway:8000
AUTH_SERVICE_URL=http://auth-service:8001
ROUTE_SERVICE_URL=http://route-service:8002
DATA_SERVICE_URL=http://data-service:8003

# CORS Configuration
CORS_ORIGINS=https://app.railwayos.com,http://localhost:3000

# Email Configuration (for reports)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@railwayos.com
SMTP_PASSWORD=app_password
REPORT_EMAIL_FROM=noreply@railwayos.com
```

## Development Deployment

### 1. Install Dependencies

```bash
# Navigate to analytics service directory
cd services/analytics-service

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Set Up Database

```bash
# Start PostgreSQL (if using Docker)
docker run -d \
  --name postgres-dev \
  -e POSTGRES_DB=railway_os \
  -e POSTGRES_USER=railway_user \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  postgres:15-alpine

# Start Redis (if using Docker)
docker run -d \
  --name redis-dev \
  -p 6379:6379 \
  redis:7-alpine

# Initialize database tables
python -c "
from shared.models import DatabaseManager
from services.analytics_service.models import create_analytics_tables
db = DatabaseManager()
create_analytics_tables(db.engine)
print('Database tables created successfully!')
"
```

### 3. Run Service Locally

```bash
# Development mode with hot reload
python -m uvicorn main:app --host 0.0.0.0 --port 8084 --reload

# Or using the module directly
python services/analytics-service/main.py
```

### 4. Verify Service

```bash
# Check health
curl http://localhost:8084/health

# Expected response
{
  "status": "healthy",
  "service": "analytics-service",
  "timestamp": "2024-01-31T10:00:00Z"
}
```

## Docker Deployment

### 1. Build Image

```bash
# From project root directory
docker build -f Dockerfile.analytics -t railway-os-analytics:latest .

# Verify image
docker images | grep analytics
```

### 2. Run Container Standalone

```bash
docker run -d \
  --name analytics-service \
  -p 8084:8084 \
  -e DATABASE_URL="postgresql://railway_user:password@postgres:5432/railway_os" \
  -e REDIS_URL="redis://redis:6379/0" \
  -e DEBUG_MODE="false" \
  -e LOG_LEVEL="INFO" \
  railway-os-analytics:latest

# Check logs
docker logs -f analytics-service
```

### 3. Verify Container

```bash
# Check if running
docker ps | grep analytics

# Check health
docker exec analytics-service curl http://localhost:8084/health

# View logs
docker logs analytics-service
```

## Docker Compose Deployment

### 1. Update Compose File

The `docker-compose.prod.yml` has already been updated with the analytics service.

### 2. Deploy Full Stack

```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
docker-compose -f docker-compose.prod.yml ps

# Expected status: all services "Up"
```

### 3. Initialize Database

```bash
# Create tables
docker-compose -f docker-compose.prod.yml exec analytics-service \
  python -c "
from shared.models import DatabaseManager
from services.analytics_service.models import create_analytics_tables
db = DatabaseManager()
create_analytics_tables(db.engine)
"

# Verify tables created
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U railway_user -d railway_os -c "
SELECT tablename FROM pg_tables 
WHERE schemaname NOT IN ('pg_catalog', 'information_schema') 
ORDER BY tablename;
"
```

### 4. Verify Deployment

```bash
# Check all services are healthy
docker-compose -f docker-compose.prod.yml ps

# Check analytics service specifically
curl http://localhost:8084/health

# Check logs
docker-compose -f docker-compose.prod.yml logs analytics-service
```

## Kubernetes Deployment

### 1. Create Kubernetes Manifests

```yaml
# k8s/analytics-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: analytics-service
  namespace: railway-os
spec:
  replicas: 2
  selector:
    matchLabels:
      app: analytics-service
  template:
    metadata:
      labels:
        app: analytics-service
    spec:
      containers:
      - name: analytics-service
        image: railway-os/analytics-service:latest
        ports:
        - containerPort: 8084
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: analytics-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: analytics-config
              key: redis-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8084
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8084
          initialDelaySeconds: 10
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: analytics-service
  namespace: railway-os
spec:
  selector:
    app: analytics-service
  ports:
  - protocol: TCP
    port: 8084
    targetPort: 8084
  type: ClusterIP
```

### 2. Create Secrets and ConfigMaps

```bash
# Create secrets
kubectl create secret generic analytics-secrets \
  --from-literal=database-url='postgresql://user:password@postgres:5432/railway_os' \
  -n railway-os

# Create configmaps
kubectl create configmap analytics-config \
  --from-literal=redis-url='redis://redis:6379/0' \
  -n railway-os
```

### 3. Deploy to Kubernetes

```bash
# Deploy
kubectl apply -f k8s/analytics-deployment.yaml

# Check deployment status
kubectl get deployments -n railway-os
kubectl get pods -n railway-os

# Check service
kubectl get svc analytics-service -n railway-os

# Port forward for testing
kubectl port-forward svc/analytics-service 8084:8084 -n railway-os

# Check logs
kubectl logs -n railway-os deployment/analytics-service
```

## Production Deployment Checklist

### Pre-Deployment
- [ ] Environment variables configured
- [ ] Database credentials secured
- [ ] Redis connection configured
- [ ] CORS origins configured
- [ ] Email settings configured (if needed)
- [ ] Logging aggregation set up
- [ ] Monitoring tools configured
- [ ] Backup strategy in place

### Deployment
- [ ] Docker image built and tested
- [ ] Image pushed to registry
- [ ] Database tables initialized
- [ ] Service deployed
- [ ] Health checks passing
- [ ] API endpoints responding
- [ ] Database connectivity verified
- [ ] Redis connectivity verified

### Post-Deployment
- [ ] Logs being collected
- [ ] Metrics being exported
- [ ] Alerts configured
- [ ] Performance baseline established
- [ ] Database backups running
- [ ] Scaling policies configured
- [ ] SSL/TLS configured
- [ ] Documentation updated

## Data Migration

### Backfill Historical Data

```python
# backfill_analytics.py
import asyncio
from datetime import datetime, timedelta
from uuid import UUID
from services.analytics_service.etl_pipeline import AnalyticsETLPipeline
from shared.models import DatabaseManager

async def backfill_analytics():
    db_manager = DatabaseManager()
    pipeline = AnalyticsETLPipeline(db_manager)
    
    tenant_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 31)
    
    await pipeline.backfill_analytics(tenant_id, start_date, end_date)

# Run
asyncio.run(backfill_analytics())
```

### Verify Data

```bash
# Check data was imported
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U railway_user -d railway_os -c "
SELECT COUNT(*) FROM tenant_550e8400e29b41d4a716446655440000.analytics_metrics;
SELECT COUNT(*) FROM tenant_550e8400e29b41d4a716446655440000.api_metrics;
SELECT COUNT(*) FROM tenant_550e8400e29b41d4a716446655440000.route_search_metrics;
"
```

## Monitoring Setup

### Prometheus Configuration

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'analytics-service'
    static_configs:
      - targets: ['localhost:8084']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Analytics Service Dashboard",
    "panels": [
      {
        "title": "Query Latency",
        "targets": [
          {
            "expr": "rate(analytics_query_duration_seconds[5m])"
          }
        ]
      },
      {
        "title": "Cache Hit Rate",
        "targets": [
          {
            "expr": "analytics_cache_hit_rate"
          }
        ]
      }
    ]
  }
}
```

### Alert Rules

```yaml
# alerts.yaml
groups:
  - name: analytics_alerts
    rules:
      - alert: AnalyticsServiceDown
        expr: up{job="analytics-service"} == 0
        for: 5m
        annotations:
          summary: "Analytics service is down"

      - alert: HighQueryLatency
        expr: rate(analytics_query_duration_seconds[5m]) > 5
        annotations:
          summary: "Analytics queries are slow"

      - alert: LowCacheHitRate
        expr: analytics_cache_hit_rate < 0.7
        annotations:
          summary: "Cache hit rate is below 70%"
```

## Scaling Configuration

### Horizontal Scaling

```yaml
# docker-compose.prod.yml (update analytics-service)
analytics-service:
  # ... existing configuration ...
  deploy:
    replicas: 3  # Increase replicas
    resources:
      limits:
        memory: 1G
        cpus: '0.75'
```

### Load Balancing

Update API Gateway to distribute requests:
```python
# Load balance across multiple analytics instances
ANALYTICS_SERVICE_URLS = [
    "http://analytics-service-1:8084",
    "http://analytics-service-2:8084",
    "http://analytics-service-3:8084"
]

def get_analytics_url():
    # Simple round-robin
    return random.choice(ANALYTICS_SERVICE_URLS)
```

## Backup & Recovery

### Database Backup

```bash
# Create backup
docker-compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U railway_user railway_os > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U railway_user railway_os < backup_20240131_100000.sql
```

### Automated Backups

```bash
# Create backup script
#!/bin/bash
BACKUP_DIR="/backups"
BACKUP_FILE="$BACKUP_DIR/analytics_backup_$(date +%Y%m%d_%H%M%S).sql"

docker-compose exec -T postgres \
  pg_dump -U railway_user railway_os > "$BACKUP_FILE"

# Keep only last 7 days
find "$BACKUP_DIR" -name "analytics_backup_*.sql" -mtime +7 -delete

# Run via cron
0 2 * * * /path/to/backup_script.sh
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker logs analytics-service

# Check database connectivity
docker exec analytics-service \
  python -c "
import asyncpg
import asyncio

async def test():
    conn = await asyncpg.connect('postgresql://user:password@postgres:5432/railway_os')
    await conn.close()

asyncio.run(test())
"
```

### Slow Queries

```bash
# Check query performance
docker-compose exec postgres \
  psql -U railway_user -d railway_os -c "
SELECT query, mean_exec_time 
FROM pg_stat_statements 
WHERE mean_exec_time > 1000 
ORDER BY mean_exec_time DESC LIMIT 10;
"
```

### Memory Issues

```bash
# Check memory usage
docker stats analytics-service

# If memory high, optimize:
# 1. Increase cache TTL
# 2. Reduce batch sizes
# 3. Add more workers
```

## Rollback Procedure

```bash
# If deployment has issues, rollback to previous version
docker-compose -f docker-compose.prod.yml down

# Deploy previous version
docker pull railway-os/analytics-service:previous-tag

# Update docker-compose and restart
docker-compose -f docker-compose.prod.yml up -d
```

## Post-Deployment Validation

```bash
# Run API tests
curl -X GET http://localhost:8084/health
curl -X POST http://localhost:8084/v1/analytics/query \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "test-tenant", "metrics": ["route_popularity"]}'

# Check database
docker-compose exec postgres \
  psql -U railway_user -d railway_os -l

# Verify all services
docker-compose -f docker-compose.prod.yml ps
```

## Performance Tuning

### Database Optimization

```sql
-- Analyze statistics
ANALYZE;

-- Vacuum tables
VACUUM FULL;

-- Reindex if necessary
REINDEX DATABASE railway_os;
```

### Cache Optimization

```python
# Adjust cache TTL
ANALYTICS_CONFIG['cache_ttl'] = 600  # 10 minutes

# Monitor cache
redis_info = redis_client.info('memory')
print(f"Memory used: {redis_info['used_memory_human']}")
```

## Documentation References

- [README.md](./README.md) - Service overview
- [API.md](./API.md) - API documentation
- [INTEGRATION.md](./INTEGRATION.md) - Integration guide
- [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) - Implementation details

## Support Contacts

- Platform Team: platform@railwayos.com
- DevOps Team: devops@railwayos.com
- On-Call: +1-XXX-XXX-XXXX

---

**Last Updated**: 2024-01-31
**Version**: 1.0.0