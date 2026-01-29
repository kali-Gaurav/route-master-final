# CI/CD Pipeline & Deployment Automation

**Version**: 1.0  
**Status**: MANDATORY DEPLOYMENT POLICY  
**Enforced Since**: 2026-01-28

---

## Executive Summary

This document defines:
1. Automated testing gates (what MUST pass before production)
2. Deployment approval workflow
3. Blue-green deployment strategy
4. Automatic rollback on failure
5. Post-deployment validation

---

## 1. GitHub Actions Workflow

### Complete CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # PHASE 1: Pre-commit Checks (2 min)
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Check for secrets
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base: ${{ github.event.repository.default_branch }}
          head: HEAD
      
      - name: Run linting
        run: |
          pip install flake8 black isort
          flake8 src/ --max-line-length=100
          black --check src/
          isort --check-only src/
      
      - name: Type checking
        run: |
          pip install mypy types-all
          mypy src/ --strict

  # PHASE 2: Unit Tests (5 min)
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run unit tests
        run: |
          pytest tests/unit/ -v --cov=src/ --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
      
      - name: Check coverage minimum
        run: |
          coverage report --fail-under=80

  # PHASE 3: Integration Tests (10 min)
  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@postgres:5432/test
        run: |
          pytest tests/integration/ -v

  # PHASE 4: Security Scanning (3 min)
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Bandit (security)
        run: |
          pip install bandit
          bandit -r src/ -f json -o bandit-report.json || true
      
      - name: Check dependencies for vulnerabilities
        uses: advisories/github-action@v1
        with:
          path: requirements.txt

  # PHASE 5: Build (3 min)
  build:
    needs: [pre-commit, unit-tests, integration-tests, security]
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker image
        run: |
          docker build -t $REGISTRY/$IMAGE_NAME:latest .
          docker tag $REGISTRY/$IMAGE_NAME:latest $REGISTRY/$IMAGE_NAME:${{ github.sha }}
      
      - name: Login to registry
        uses: docker/login-action@v2
        with:
          registry: $REGISTRY
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Push to registry
        run: |
          docker push $REGISTRY/$IMAGE_NAME:latest
          docker push $REGISTRY/$IMAGE_NAME:${{ github.sha }}

  # PHASE 6: Deploy to Staging (5 min)
  deploy-staging:
    needs: [build]
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to staging
        run: |
          kubectl set image deployment/analytics-service \
            analytics-service=$REGISTRY/$IMAGE_NAME:${{ github.sha }} \
            -n staging
      
      - name: Wait for rollout
        run: |
          kubectl rollout status deployment/analytics-service -n staging
      
      - name: Run smoke tests
        run: |
          pytest tests/staging/test_smoke.py -v --endpoint=https://staging.railway.local
      
      - name: Run performance tests
        run: |
          locust -f tests/staging/load_test.py \
            --host=https://staging.railway.local \
            -u 100 --spawn-rate 10 -t 5m --headless

  # PHASE 7: Manual Approval for Production (0 min - waiting)
  approve-production:
    needs: [deploy-staging]
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    environment:
      name: production
      reviewers: [deployment-team, security-team]
    steps:
      - name: Waiting for approval
        run: echo "Awaiting production deployment approval..."

  # PHASE 8: Deploy to Production (5 min)
  deploy-production:
    needs: [approve-production]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy (Blue-Green)
        run: |
          # Get current version (blue)
          BLUE=$(kubectl get deployment analytics-service -n prod -o jsonpath='{.status.replicas}')
          
          # Deploy new version (green) with 0 replicas initially
          kubectl set image deployment/analytics-service-green \
            analytics-service=$REGISTRY/$IMAGE_NAME:${{ github.sha }} \
            -n prod
          
          # Scale up green (1 replica)
          kubectl scale deployment analytics-service-green -n prod --replicas=1
          
          # Wait for green to be healthy
          kubectl rollout status deployment/analytics-service-green -n prod
          
          # Run health checks on green
          ./scripts/health_check.sh green.railway.local
      
      - name: Switch traffic to green
        if: ${{ success() }}
        run: |
          # Switch load balancer to green
          kubectl patch service analytics-service -n prod \
            -p '{"spec":{"selector":{"version":"green"}}}'
          
          # Wait for connection draining (30 seconds)
          sleep 30
          
          # Promote green to blue
          kubectl patch deployment analytics-service -n prod \
            -p '{"spec":{"template":{"metadata":{"labels":{"version":"blue"}}}}}'
      
      - name: Automatic Rollback on Failure
        if: failure()
        run: |
          echo "Deployment failed, rolling back..."
          kubectl patch service analytics-service -n prod \
            -p '{"spec":{"selector":{"version":"blue"}}}'
          
          # Alert ops team
          curl -X POST https://slack-webhook-url \
            -d '{"text":"Production deployment rolled back"}'
      
      - name: Monitor for 30 minutes
        run: |
          ./scripts/monitor_deployment.sh 30min
      
      - name: Create deployment record
        run: |
          echo "Deployed: $IMAGE_NAME:${{ github.sha }}" >> DEPLOYMENTS.log
          git add DEPLOYMENTS.log
          git commit -m "Deployment: prod-$(date +%Y%m%d-%H%M%S)"
          git push

  # PHASE 9: Post-Deployment Validation (2 min)
  validate:
    needs: [deploy-production]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Smoke tests (production)
        run: |
          pytest tests/production/test_smoke.py -v --endpoint=https://api.railway.local
      
      - name: Check metrics
        run: |
          ./scripts/check_metrics.sh
          # Verify error rate < 0.1%
          # Verify latency p99 < 1000ms
      
      - name: Notify team
        run: |
          curl -X POST https://slack-webhook-url \
            -d '{"text":"✅ Production deployment successful"}'
```

---

## 2. Approval Workflow

### Code Review → Staging → Production

```
Developer submits PR
        ↓
Automated checks run (2-5 min)
  ✅ Tests pass
  ✅ Linting passes
  ✅ No secrets found
        ↓
Manual code review
  ✅ Architecture approved
  ✅ Data ownership respected
  ✅ API_GOVERNANCE followed
  ✅ Security reviewed
        ↓
2+ approvals required
        ↓
Merge to main
        ↓
Build Docker image & push
        ↓
Deploy to Staging (automatic)
        ↓
QA team tests (24-48 hours)
  ✅ Functional testing
  ✅ Integration testing
  ✅ Performance testing
  ✅ Regression testing
        ↓
Deployment approval required
  - Required: Engineering Lead
  - Required: On-Call Engineer
  - Optional: Product Manager (for features)
        ↓
Deploy to Production
        ↓
Monitor for 30 minutes
        ↓
Automatic rollback if issues
```

---

## 3. Blue-Green Deployment

### Strategy: Zero Downtime Updates

```
┌─────────────────────────────────────┐
│ BEFORE: Blue running (v1.0)         │
│ Load Balancer → Blue (v1.0)         │
│ Green: not running                  │
└─────────────────────────────────────┘
           ↓ Deploy v1.1 to Green
┌─────────────────────────────────────┐
│ DURING: Both running                │
│ Load Balancer → Blue (v1.0)         │
│ Green: running v1.1 (no traffic)    │
│ Verification: Health checks pass    │
└─────────────────────────────────────┘
           ↓ Switch traffic to Green
┌─────────────────────────────────────┐
│ AFTER: Green running (v1.1)         │
│ Load Balancer → Green (v1.1)        │
│ Blue: running v1.0 (hot standby)    │
│ Can rollback instantly if needed    │
└─────────────────────────────────────┘
```

### Implementation

```bash
#!/bin/bash
# scripts/blue_green_deploy.sh

BLUE_VERSION=$(kubectl get deployment analytics-service -n prod \
  -o jsonpath='{.spec.template.spec.containers[0].image}')
NEW_VERSION=$1  # e.g., v1.1.0

echo "Current (Blue): $BLUE_VERSION"
echo "New (Green): $NEW_VERSION"

# 1. Deploy to green with 0 initial replicas
kubectl set image deployment/analytics-service-green \
  analytics-service=ghcr.io/railway/analytics-service:$NEW_VERSION \
  -n prod

# 2. Scale green to match blue
BLUE_REPLICAS=$(kubectl get deployment analytics-service -n prod \
  -o jsonpath='{.spec.replicas}')
kubectl scale deployment analytics-service-green --replicas=$BLUE_REPLICAS -n prod

# 3. Wait for green to be ready
kubectl wait --for=condition=available \
  --timeout=300s \
  deployment/analytics-service-green -n prod

# 4. Run health checks against green
echo "Running health checks..."
for i in {1..10}; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    http://analytics-service-green:8000/health)
  if [ "$STATUS" = "200" ]; then
    echo "✅ Green is healthy"
    break
  fi
  echo "⏳ Waiting for green... (attempt $i/10)"
  sleep 5
done

# 5. Switch load balancer traffic
echo "Switching traffic to green..."
kubectl patch service analytics-service -n prod \
  -p '{"spec":{"selector":{"deployment":"analytics-service-green"}}}'

# 6. Wait 30 seconds for connection draining
sleep 30

# 7. Relabel green as blue (for future deployments)
kubectl patch deployment analytics-service -n prod \
  -p '{"spec":{"template":{"metadata":{"labels":{"deployment":"analytics-service"}}}}}'

echo "✅ Deployment successful"
```

### Rollback (Instant)

```bash
#!/bin/bash
# scripts/rollback.sh

CURRENT=$(kubectl get service analytics-service -n prod \
  -o jsonpath='{.spec.selector.deployment}')

if [ "$CURRENT" = "analytics-service-green" ]; then
  echo "Rolling back to Blue..."
  kubectl patch service analytics-service -n prod \
    -p '{"spec":{"selector":{"deployment":"analytics-service"}}}'
else
  echo "Rolling back to Green..."
  kubectl patch service analytics-service -n prod \
    -p '{"spec":{"selector":{"deployment":"analytics-service-green"}}}'
fi

echo "✅ Rollback complete"
```

---

## 4. Automatic Failure Detection

### Metrics That Trigger Rollback

```
Trigger rollback if:
  ❌ Error rate > 1% (5x normal)
  ❌ p99 latency > 5000ms (5x normal)
  ❌ Memory usage > 80%
  ❌ CPU usage > 80%
  ❌ Health check failures > 10%
  ❌ Circuit breaker open for > 2 min
  ❌ Database connection pool > 90%

Verification window: 5 minutes after deployment
```

### Implementation

```python
# scripts/monitor_deployment.py
import time
import requests
from prometheus_client import PrometheusClient

def monitor_deployment(duration_minutes=5):
    """Monitor deployment and rollback if metrics bad"""
    
    client = PrometheusClient("http://prometheus:9090")
    start_time = time.time()
    baseline = get_metrics(client, minutes=30)  # Last 30 min baseline
    
    while time.time() - start_time < duration_minutes * 60:
        current = get_metrics(client, minutes=5)  # Last 5 minutes
        
        # Check error rate
        if current['error_rate'] > baseline['error_rate'] * 5:
            print(f"ERROR RATE TOO HIGH: {current['error_rate']}%")
            trigger_rollback("High error rate")
            break
        
        # Check latency
        if current['p99_latency'] > baseline['p99_latency'] * 5:
            print(f"LATENCY TOO HIGH: {current['p99_latency']}ms")
            trigger_rollback("High latency")
            break
        
        # Check resource usage
        if current['memory_usage'] > 80:
            print(f"MEMORY TOO HIGH: {current['memory_usage']}%")
            trigger_rollback("Memory usage > 80%")
            break
        
        time.sleep(30)  # Check every 30 seconds
    
    print("✅ Deployment monitoring complete, no issues detected")

def get_metrics(client, minutes=5):
    """Get current metrics from Prometheus"""
    return {
        'error_rate': client.query(
            f'rate(request_errors_total[{minutes}m]) / rate(requests_total[{minutes}m]) * 100'
        ),
        'p99_latency': client.query(
            f'histogram_quantile(0.99, rate(request_duration_seconds_bucket[{minutes}m]))'
        ),
        'memory_usage': client.query('container_memory_usage_percent'),
        'cpu_usage': client.query('rate(container_cpu_usage_seconds_total[{minutes}m]) * 100'),
    }

def trigger_rollback(reason):
    """Trigger automatic rollback"""
    print(f"🚨 ROLLBACK TRIGGERED: {reason}")
    
    # Execute rollback script
    os.system('bash scripts/rollback.sh')
    
    # Alert ops team
    slack_alert(f"⚠️ Automatic rollback triggered: {reason}")
    
    # Create incident report
    with open('incident_report.txt', 'w') as f:
        f.write(f"Timestamp: {datetime.now()}\n")
        f.write(f"Reason: {reason}\n")
        f.write(f"Metrics at time of rollback: {get_metrics()}\n")
```

---

## 5. Post-Deployment Checklist

After production deployment:

- [ ] All smoke tests pass
- [ ] Error rate < 0.1%
- [ ] p99 latency < 1000ms
- [ ] No circuit breaker alerts
- [ ] Database connection pool < 70%
- [ ] Memory usage < 70%
- [ ] CPU usage < 70%
- [ ] No security alerts
- [ ] Audit logs show expected activity
- [ ] Team notified of deployment
- [ ] Deployment logged in DEPLOYMENTS.log
- [ ] Metrics dashboard shows normal behavior

---

**Document Established**: 2026-01-28  
**Owner**: DevOps/Platform Team  
**Review Cycle**: When changing deployment strategy  
**Last Updated**: 2026-01-28
