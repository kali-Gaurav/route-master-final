# Secrets Management Strategy

**Version**: 1.0  
**Status**: MANDATORY SECURITY REQUIREMENT  
**Enforced Since**: 2026-01-28

---

## Executive Summary

This document defines:
1. What qualifies as a secret
2. Where secrets are stored per environment
3. How secrets are rotated
4. Emergency access procedures
5. Secret leakage detection & remediation

---

## 1. Secret Classification

### What IS a Secret?

```
✅ DATABASE CREDENTIALS
   - PostgreSQL password
   - Connection string with password
   - Service account credentials

✅ API KEYS & TOKENS
   - AWS IAM keys
   - External API keys (Stripe, SendGrid, etc.)
   - OAuth client secrets
   - JWT signing keys

✅ ENCRYPTION KEYS
   - Master encryption key
   - Data encryption keys
   - Database encryption key

✅ CERTIFICATES
   - TLS certificates (private key)
   - mTLS client certificates
   - Code signing certificates

✅ ACCESS TOKENS
   - Third-party service access tokens
   - SSH keys
   - GPG keys

✅ SENSITIVE CONFIG
   - Database host (production only)
   - Internal service URLs (production only)
   - Feature flags with security implications
```

### What IS NOT a Secret?

```
❌ SERVICE NAMES
   - "analytics-service"
   - "route-service"
   - Published in documentation

❌ GENERAL CONFIGURATION
   - Timeout values (5 seconds)
   - Page size (100 items)
   - Logging level (DEBUG, INFO)
   - Cache TTL (30 minutes)

❌ FEATURE FLAGS
   - "enable_new_dashboard" (unless security-related)
   - "percentage_of_users_on_v2" (unless security-related)

❌ VERSION NUMBERS
   - API versions (/v1, /v2)
   - Service versions (1.2.3)
```

---

## 2. Secret Storage by Environment

### Development Environment

**Storage**: Local .env file (NEVER commit to Git)

```bash
# .env (local, gitignored)
DATABASE_URL=postgresql://admin:dev_password@localhost:5432/railway_dev
REDIS_URL=redis://localhost:6379
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
JWT_SECRET_KEY=dev-secret-key-only-for-local-testing
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

**Rules**:
- ❌ NEVER commit .env to Git
- ❌ NEVER use production secrets locally
- ✅ Use weak passwords (it's local only)
- ✅ Reset daily with fresh test data
- ✅ Share via encrypted password manager (not email)

**Access**:
```bash
# Copy from vault to local
1pass get railway-dev-env > .env

# Load in terminal
export $(cat .env | xargs)

# Or use docker-compose environment
docker-compose -f docker-compose.dev.yml up
```

### Staging Environment

**Storage**: AWS Secrets Manager (managed by Terraform)

```hcl
# terraform/staging/secrets.tf
resource "aws_secretsmanager_secret" "database_password" {
  name                    = "staging/database/password"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "database_password" {
  secret_id       = aws_secretsmanager_secret.database_password.id
  secret_string   = random_password.db_password.result
}

resource "aws_secretsmanager_secret" "jwt_key" {
  name = "staging/jwt/secret_key"
}

resource "aws_secretsmanager_secret_version" "jwt_key" {
  secret_id     = aws_secretsmanager_secret.jwt_key.id
  secret_string = random_password.jwt_key.result
}
```

**Access**:
```python
# analytics_service/config.py
import boto3
import json

def get_secrets(environment: str = "staging"):
    """Get secrets from AWS Secrets Manager"""
    client = boto3.client('secretsmanager')
    
    # Get all secrets for environment
    response = client.list_secrets(
        Filters=[{'Key': 'name', 'Values': [f'{environment}/']}]
    )
    
    secrets = {}
    for secret in response['SecretList']:
        secret_value = client.get_secret_value(SecretId=secret['Name'])
        secrets[secret['Name']] = json.loads(secret_value['SecretString'])
    
    return secrets

# Load at startup
SECRETS = get_secrets(environment=os.environ['APP_ENV'])
DATABASE_URL = SECRETS['staging/database/password']
JWT_SECRET = SECRETS['staging/jwt/secret_key']
```

**Permissions**:
```yaml
# kubernetes/staging/service-account.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: analytics-service
  namespace: staging

---
apiVersion: iam.amazonaws.com/v1
kind: IAMPolicyAttachment
metadata:
  name: analytics-secrets-policy
policy:
  Version: '2012-10-17'
  Statement:
    - Effect: Allow
      Action:
        - secretsmanager:GetSecretValue
        - secretsmanager:DescribeSecret
      Resource: arn:aws:secretsmanager:*:*:secret:staging/*
```

### Production Environment

**Storage**: AWS Secrets Manager (with encryption, audit logging, rotation)

```hcl
# terraform/production/secrets.tf
resource "aws_secretsmanager_secret" "database_password" {
  name                    = "prod/database/password"
  description             = "Production database password"
  recovery_window_in_days = 30
  kms_key_id              = aws_kms_key.production.id
  
  tags = {
    Environment = "production"
    Rotation    = "required"
  }
}

# Automatic rotation every 90 days
resource "aws_secretsmanager_secret_rotation" "database_password" {
  secret_id           = aws_secretsmanager_secret.database_password.id
  rotation_lambda_arn = aws_lambda_function.rotate_secret.arn
  
  rotation_rules {
    automatically_after_days = 90
  }
}

resource "aws_secretsmanager_secret_version" "database_password" {
  secret_id       = aws_secretsmanager_secret.database_password.id
  secret_string   = random_password.db_password.result
  version_stages  = ["AWSCURRENT"]
}
```

**Encryption**:
```
Each secret encrypted with AWS KMS
Master key: Only ops team can access
Encryption: AES-256
Audit trail: CloudTrail logs all access
```

**Access Audit**:
```
CloudTrail logs every secret access:
  - Who accessed it (service/user)
  - When (timestamp)
  - What (which secret)
  - From where (IP address)

Alerts triggered if:
  - Accessed from unexpected IP
  - Accessed outside business hours
  - Accessed by unexpected service
  - Multiple failed access attempts
```

---

## 3. Secret Rotation

### Rotation Strategy

```
Development:
  Manual rotation (not critical)
  When: Updated whenever team rebuilds

Staging:
  Automatic rotation every 90 days
  No downtime (Secrets Manager handles it)
  
Production:
  Automatic rotation every 30 days (more frequent)
  Gradual rollout to avoid issues
  
Critical Secrets (database password):
  Rotation every 30 days
  
Less Critical (API keys):
  Rotation every 90 days
```

### Rotation Procedure

```
1. Generate new secret
   - Random password (32 chars, mixed types)
   - AWS Secrets Manager generates automatically

2. Test with new secret
   - Lambda function tests connection
   - Verify service can use new secret
   - If fails: rollback to old secret

3. Activate new secret
   - Update all references to new secret
   - Keep old secret for 30 days (fallback)

4. Update infrastructure
   - RDS password updated
   - Kubernetes pods restart
   - New environment variables injected

5. Archive old secret
   - Keep in Secrets Manager for 30 days
   - Then delete permanently

No downtime, automatic, audited.
```

### Rotation Lambda (Example)

```python
# lambda/rotate_secret.py
import boto3
import json
import psycopg2

def rotate_secret(event, context):
    """Rotate database password"""
    
    client = boto3.client('secretsmanager')
    
    # Parse event
    secret_id = event['SecretId']
    token = event['ClientRequestToken']
    step = event['Step']
    
    if step == 'create':
        # Generate new password
        new_password = generate_password(32)
        
        # Store tentative secret
        client.put_secret_value(
            SecretId=secret_id,
            ClientRequestToken=token,
            SecretString=json.dumps({
                'username': 'admin',
                'password': new_password
            }),
            VersionStages=['AWSPENDING']
        )
    
    elif step == 'set':
        # Update database with new password
        db = psycopg2.connect(
            host='prod-db.rds.amazonaws.com',
            user='admin',
            password=get_current_password(secret_id),
            database='railway_prod'
        )
        cursor = db.cursor()
        new_password = get_pending_password(secret_id, token)
        cursor.execute(f"ALTER USER admin WITH PASSWORD '{new_password}'")
        db.commit()
    
    elif step == 'test':
        # Test connection with new password
        new_password = get_pending_password(secret_id, token)
        db = psycopg2.connect(
            host='prod-db.rds.amazonaws.com',
            user='admin',
            password=new_password,
            database='railway_prod'
        )
        db.close()
    
    elif step == 'finish':
        # Mark new secret as current
        client.update_secret_version_stage(
            SecretId=secret_id,
            VersionStages=['AWSCURRENT'],
            MoveToVersionId=token,
            RemoveFromVersionId=get_current_version(secret_id)
        )
```

---

## 4. Emergency Access

### Scenario: Urgent Production Bug

**Situation**: Production database is down, need immediate access

```
1. Declare emergency
   - Slack: @security-on-call "EMERGENCY: Prod DB down, need access"
   - Trigger: PagerDuty alert

2. Get temporary access
   - Two approvals required (team lead + security)
   - Approvals must happen within 5 minutes
   
3. Access granted
   - One-time session started
   - Access expires in 1 hour
   - All actions logged
   
4. Use access
   - Connect to database
   - Diagnose and fix issue
   - All queries logged with timestamp
   
5. Access revoked
   - Session expires after 1 hour
   - Password rotated immediately (within 15 minutes)
   - Post-incident review within 24 hours
```

### Emergency Access Procedure

```bash
# Emergency access request
aws secretsmanager get-secret-value \
  --secret-id prod/database/password \
  --reason "EMERGENCY: Prod DB connectivity issue" \
  --emergency-access

# Requires:
# 1. MFA authentication
# 2. Two-person approval
# 3. Security policy acknowledgment

# Result: One-time access granted for 1 hour
```

---

## 5. Secret Leakage Detection & Remediation

### Detection Methods

```
GitHub secret scanning:
  - Scans commits for API keys, passwords
  - Prevents secrets from being committed
  - Real-time alerts on suspicious pushes

CloudTrail audit logs:
  - Alerts on unusual secret access patterns
  - Detects IP spoofing, unusual times
  - Alerts on failed access attempts

Secret rotation:
  - If old secret used after rotation, alert
  - Indicates potential compromise
  - Immediate investigation triggered
```

### If Secret Is Leaked

```
1. IMMEDIATE (Within 5 minutes)
   - Revoke the leaked secret
   - Rotate to new secret
   - Alert security team
   - Notify affected services

2. SHORT-TERM (Within 30 minutes)
   - Investigate: How was it leaked?
   - Check audit logs for unauthorized access
   - Review who had access
   - Identify extent of exposure

3. MEDIUM-TERM (Within 24 hours)
   - Post-incident review
   - Determine root cause
   - Implement preventative measures
   - Document incident

4. LONG-TERM (Within 1 week)
   - Update training on secret management
   - Audit all secret access
   - Review security policies
   - Update detection systems
```

### Example: API Key Leaked

```
1. GitHub detects API key in commit
2. Pre-commit hook blocks push
3. Developer notified: "API key detected in code"
4. Developer must:
   - Remove from code
   - Revoke leaked key
   - Request new key from ops
   - Re-commit without secret

Alternatively, if already pushed:
1. GitHub secret scanning detects
2. Alert to security team
3. GitHub automatically revokes on provider side
4. Ops rotates secret
5. Services restarted with new secret
6. Incident logged

No downtime if caught early.
```

---

## 6. Secret Management Checklist

Before deploying service:

- [ ] All credentials moved to Secrets Manager (production)
- [ ] .env file exists but is gitignored
- [ ] No secrets in code (grep for passwords, API keys)
- [ ] No secrets in logs (structured logging reviewed)
- [ ] No secrets in error messages
- [ ] Rotation policy defined for each secret
- [ ] Access controls configured (who can read?)
- [ ] Audit logging enabled
- [ ] Emergency access procedure documented
- [ ] Team trained on secret management
- [ ] Secret leakage detection enabled (GitHub, CloudTrail)
- [ ] Incident response plan reviewed

---

**Document Established**: 2026-01-28  
**Owner**: Security Team  
**Review Cycle**: When adding new secrets or changing rotation policy  
**Last Updated**: 2026-01-28
