# Deployment Architecture & Environment Separation

**Version**: 1.0  
**Status**: MANDATORY DEPLOYMENT POLICY  
**Enforced Since**: 2026-01-28

---

## Executive Summary

This document defines:
1. How environments are separate (Dev, Staging, Production)
2. Promotion path for code and data
3. Secrets management per environment
4. Infrastructure as Code (IaC) approach
5. Disaster recovery procedures

---

## 1. Environment Architecture

### Three Isolated Environments

```
┌──────────────┐
│ DEVELOPMENT  │
│ (Local)      │
│ 1 developer  │
└────┬─────────┘
     │ Code review
     ↓
┌──────────────┐
│ STAGING      │
│ (QA Cluster) │
│ Test data    │
└────┬─────────┘
     │ Approval
     ↓
┌──────────────┐
│ PRODUCTION   │
│ (Cloud)      │
│ Real data    │
└──────────────┘
```

### Development Environment

**Purpose**: Developer machine, local testing

```
- PostgreSQL: docker-compose (local)
- Redis: docker-compose (local)
- RabbitMQ: docker-compose (local)
- Services: Run locally in IDE or Docker
- Data: Synthetic test data (reset daily)
- Secrets: Read from .env (NEVER commit)
- Scale: Single node (no HA)
```

**Setup**:
```bash
# Start dev environment
docker-compose -f docker-compose.dev.yml up

# Create test database
python -m scripts.reset_dev_db

# Run services
python -m analytics_service.main  # Terminal 1
python -m route_service.main      # Terminal 2
python -m frontend.main           # Terminal 3
```

### Staging Environment

**Purpose**: QA testing before production release

```
- PostgreSQL: Managed RDS (AWS)
- Redis: Elasticache (AWS)
- RabbitMQ: AWS MQ
- Services: Kubernetes (3 replicas per service)
- Data: Snapshot of production (7 days old, anonymized)
- Secrets: AWS Secrets Manager
- Scale: HA cluster (automatic failover)
```

**Configuration**:
```yaml
# kubernetes/staging/values.yaml
environment: staging
replicas:
  analytics-service: 3
  route-service: 2
  auth-service: 2
database:
  host: staging-db.rds.amazonaws.com
  name: railway_staging
  pool_size: 20
redis:
  host: staging-redis.elasticache.amazonaws.com
secrets:
  source: aws-secrets-manager
  prefix: staging/
```

### Production Environment

**Purpose**: Real users, real data

```
- PostgreSQL: Managed RDS (AWS) with Multi-AZ
- Redis: Elasticache with cluster mode
- RabbitMQ: AWS MQ with HA
- Services: Kubernetes on EKS (auto-scaling)
- Data: Real production data (encrypted at rest)
- Secrets: AWS Secrets Manager (rotated automatically)
- Scale: Multi-region ready
```

**Configuration**:
```yaml
# kubernetes/production/values.yaml
environment: production
replicas:
  analytics-service: 5 (auto-scale: 3-10)
  route-service: 4 (auto-scale: 2-8)
  auth-service: 3 (auto-scale: 2-6)
database:
  host: prod-db.rds.amazonaws.com
  name: railway_prod
  pool_size: 50
  multi_az: true
  backup_retention: 30
redis:
  host: prod-redis.elasticache.amazonaws.com
  cluster_mode: true
  num_nodes: 6
secrets:
  source: aws-secrets-manager
  prefix: prod/
  rotation: 90-day
```

---

## 2. Code Promotion Path

### Step 1: Develop Locally

```bash
# Create feature branch
git checkout -b feature/analytics-dashboard

# Make changes
code analytics_service/dashboard.py

# Test locally
pytest tests/test_dashboard.py -v
docker-compose -f docker-compose.dev.yml up

# Commit
git add .
git commit -m "feat: add analytics dashboard"
```

### Step 2: Code Review (GitHub)

```
Push to GitHub
  ↓
Create Pull Request
  ↓
Automated Checks:
  ✅ Unit tests pass
  ✅ Code coverage > 80%
  ✅ Linting (flake8, black)
  ✅ Type checking (mypy)
  ✅ Security scanning (bandit)
  ↓
Manual Code Review:
  ✅ Architecture alignment
  ✅ Data ownership respected
  ✅ No hardcoded secrets
  ✅ Documentation updated
  ✅ API_GOVERNANCE respected
  ↓
Approval (2+ reviewers)
```

### Step 3: Deploy to Staging

```bash
# Merge to main automatically triggers:
1. Build Docker image
   docker build -t analytics-service:v1.2.3 .

2. Push to ECR (Elastic Container Registry)
   docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/analytics-service:v1.2.3

3. Deploy to Staging Kubernetes
   kubectl set image deployment/analytics-service \
     analytics-service=123456789.dkr.ecr.us-east-1.amazonaws.com/analytics-service:v1.2.3 \
     -n staging

4. Run smoke tests
   pytest tests/staging/test_smoke.py

5. Notify team
   Slack: ✅ Deployed to staging
```

### Step 4: QA Testing in Staging

```
QA Team:
  - Functional testing (does it work?)
  - Integration testing (works with other services?)
  - Performance testing (is it fast?)
  - Security testing (no vulnerabilities?)
  - Regression testing (did we break anything?)

Duration: 24-48 hours
Status: Must pass ALL tests before production
```

### Step 5: Approve for Production

```
Stakeholders:
  ✅ QA Lead: "All tests passed"
  ✅ Architecture: "Follows SYSTEM_ARCHITECTURE"
  ✅ Security: "No vulnerabilities"
  ✅ Product: "Ready for users"

  → Tag: release/v1.2.3
  → Trigger production deployment
```

### Step 6: Deploy to Production

```bash
# Automatic (if approved) or manual (if high-risk):
1. Build Docker image (if not cached)
2. Push to ECR
3. Blue-Green Deployment:
   - Keep old version (blue) running
   - Deploy new version (green) alongside
   - Test health checks on green
   - If all good: Route traffic to green
   - If error: Route back to blue (instant rollback)
4. Run production smoke tests
5. Monitor metrics for 30 minutes
6. If issues: Automatic rollback to blue
7. Notify team
   Slack: ✅ Production deployment complete
```

---

## 3. Secrets Management

### What Is a Secret?

```
✅ Secrets:
  - Database passwords
  - API keys (AWS, external services)
  - JWT signing keys
  - Encryption keys
  - OAuth client secrets

❌ NOT secrets:
  - Configuration values (timeout, page size)
  - Feature flags
  - Logging levels
  - Service URLs (unless internal)
```

### Secret Storage by Environment

### Development

```
Store in: .env file (gitignored)
Path: railway-operating-system-microservices/.env

Example:
DATABASE_URL=postgresql://admin:dev123@localhost:5432/railway_dev
REDIS_URL=redis://localhost:6379
RABBITMQ_URL=amqp://guest:guest@localhost:5672/

ℹ️ Local only, never pushed to Git
⚠️ Use weak passwords (it's dev only)
```

### Staging

```
Store in: AWS Secrets Manager
Path: staging/analytics-service

Example:
{
  "database_url": "postgresql://admin:...@staging-db.rds.amazonaws.com:5432/railway_staging",
  "redis_url": "rediss://staging-redis.elasticache.amazonaws.com:6379",
  "api_key_external": "sk_test_..."
}

✅ Automatically injected into pods
✅ Rotated by AWS on schedule
✅ Encrypted at rest
```

### Production

```
Store in: AWS Secrets Manager
Path: prod/analytics-service

Example:
{
  "database_url": "postgresql://admin:...@prod-db.rds.amazonaws.com:5432/railway_prod",
  "redis_url": "rediss://prod-redis.elasticache.amazonaws.com:6379",
  "api_key_external": "sk_live_...",
  "encryption_master_key": "kms://arn:aws:kms:..."
}

✅ Automatically rotated (90-day)
✅ Encrypted with AWS KMS
✅ Audit logged (who accessed?)
✅ No human ever sees the value
```

### Accessing Secrets at Runtime

```python
# Python service reads from environment (injected by Kubernetes)
import os
from sqlalchemy import create_engine

db_url = os.environ['DATABASE_URL']
engine = create_engine(db_url)

# For AWS KMS encryption:
import boto3
kms_client = boto3.client('kms')
encrypted_data = os.environ['ENCRYPTED_PAYMENT_DATA']
plaintext = kms_client.decrypt(CiphertextBlob=encrypted_data)['Plaintext']
```

### Secret Rotation

```
AWS Secrets Manager handles automatically:

1. Generate new secret
2. Test with new secret
3. Update application environment
4. Rotate to new secret
5. Keep old secret for 30 days (rollback window)
6. Delete old secret

No downtime, automatic, audited.
```

---

## 4. Infrastructure as Code (IaC)

### Using Terraform

```
directory structure:
terraform/
  ├── main.tf          # Provider, backend
  ├── networking.tf    # VPC, security groups
  ├── database.tf      # RDS PostgreSQL
  ├── cache.tf         # Elasticache Redis
  ├── kubernetes.tf    # EKS cluster
  ├── staging/
  │   └── terraform.tfvars
  └── production/
      └── terraform.tfvars
```

### Define Infrastructure

```hcl
# terraform/database.tf
resource "aws_db_instance" "analytics" {
  identifier       = "railway-${var.environment}-db"
  engine           = "postgres"
  engine_version   = "14.7"
  instance_class   = var.db_instance_class
  allocated_storage = 100
  
  db_name  = "railway_${var.environment}"
  username = "admin"
  password = random_password.db_password.result
  
  # High availability
  multi_az            = var.environment == "production" ? true : false
  backup_retention_period = var.environment == "production" ? 30 : 7
  
  # Encryption
  storage_encrypted = true
  kms_key_id        = aws_kms_key.database.arn
  
  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}
```

### Deploy Infrastructure

```bash
# Initialize Terraform
cd terraform
terraform init

# Preview changes
terraform plan -var-file=staging/terraform.tfvars

# Apply changes
terraform apply -var-file=staging/terraform.tfvars -auto-approve

# Later, change to production
terraform plan -var-file=production/terraform.tfvars
terraform apply -var-file=production/terraform.tfvars
```

---

## 5. Disaster Recovery

### Backup Strategy

```
Daily:
  - Full database backup (automated by RDS)
  - Retention: 30 days (production), 7 days (staging)
  - Encryption: AWS KMS
  - Location: AWS S3 (auto replicated)

Weekly:
  - Export to S3 (long-term archive)
  - Retention: 1 year
  - Purpose: Compliance, deep historical data

Hourly (for critical tables):
  - Continuous replication to standby
  - Multi-AZ failover (automatic)
  - RPO: < 1 minute (almost 0 data loss)
```

### Recovery Procedures

### Minor Incident (Service Crash)

```
Time: 0 seconds
  1. Service crashes or circuit breaker opens
  2. Kubernetes automatically restarts pod
  3. Service back up in < 30 seconds

Recovery: Automatic, no human action needed
```

### Database Corruption

```
Time: T+0
  1. Issue detected (data quality check fails)
  2. Alert to ops team

Time: T+5 min
  1. Stop application writes (read-only mode)
  2. Identify last good backup
  3. Create point-in-time restore

Time: T+15 min
  1. Restore database from backup
  2. Verify data integrity
  3. Resume application writes

Recovery: 15 minutes, some data loss (~5 minutes)
```

### Complete Data Center Failure

```
Time: T+0
  1. Primary region fails
  2. Kubernetes detects pod failures
  3. AWS failover triggers automatically

Time: T+1-5 min
  1. Traffic routed to secondary region
  2. Services restart in secondary region
  3. Database failover to standby (Multi-AZ)

Time: T+10 min
  1. All services online in secondary region
  2. Users experience brief latency increase
  3. Operations team investigates

Recovery: < 10 minutes, automatic failover
```

### Restore from Backup

```bash
# Point-in-time restore (if available)
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier railway-prod-db \
  --db-instance-identifier railway-prod-db-restored \
  --restore-time "2026-01-28T10:00:00Z"

# Wait for restore to complete (15-30 minutes)
aws rds describe-db-instances --db-instance-identifier railway-prod-db-restored

# Test restored database
psql -h railway-prod-db-restored.rds.amazonaws.com -U admin -d railway_prod

# Switch application to restored database
# (Update connection string in Secrets Manager)

# Verify all services
pytest tests/prod/test_smoke.py

# Keep old database for comparison (1 week)
# Then delete if all good
aws rds delete-db-instance --db-instance-identifier railway-prod-db --skip-final-snapshot
```

---

## 6. Environment Parity

### What Should Be the Same

```
✅ Same:
  - Application code (same version)
  - Application logic
  - Data models (same schema)
  - API contracts (API_GOVERNANCE)
  - Monitoring/alerts (same thresholds)
  - Security policies (same rules)
  - Architecture patterns (SYSTEM_ARCHITECTURE)

❌ Different:
  - Scale (prod has more replicas)
  - Performance (prod optimized)
  - Data (dev is test, staging is anonymized, prod is real)
  - Secrets (dev is weak, staging/prod are strong)
  - Costs (dev is cheap, prod is expensive)
```

### Testing Parity

```
All tests run identically in all environments:
  - Unit tests: Dev only
  - Integration tests: Dev + Staging
  - Smoke tests: Staging + Production
  - Performance tests: Staging only (prod is live)
  - Security tests: Staging + Production

Result: Staging behaves like production → can catch issues early
```

---

## 7. Deployment Checklist

Before deploying to production:

- [ ] All tests pass (unit, integration, smoke)
- [ ] Code review approved (2+ reviewers)
- [ ] No hardcoded secrets in code
- [ ] Database schema migration tested
- [ ] Metrics and alerts configured
- [ ] Runbook updated (how to fix if things break?)
- [ ] Communication plan (how to notify users?)
- [ ] Rollback plan (how to go back if needed?)
- [ ] Health checks configured
- [ ] Load tested
- [ ] Security reviewed
- [ ] Compliance reviewed
- [ ] Capacity planned (do we have enough resources?)
- [ ] Stakeholder approval obtained

---

**Document Established**: 2026-01-28  
**Owner**: DevOps/SRE Team  
**Review Cycle**: When adding new environments  
**Last Updated**: 2026-01-28
