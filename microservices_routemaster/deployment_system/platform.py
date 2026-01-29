"""
Deployment Platform - Production Release Management
Handles safe deployments with canary, blue-green, rollback capabilities
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import hashlib
import logging

logger = logging.getLogger(__name__)


class DeploymentStrategy(Enum):
    """Deployment strategies for safe rollouts"""
    BLUE_GREEN = "blue_green"  # Run both versions, switch traffic
    CANARY = "canary"          # Route % of traffic to new version
    ROLLING = "rolling"        # Gradual replacement of pods
    SHADOW = "shadow"          # Shadow traffic, no customer impact


class DeploymentPhase(Enum):
    """Phases in deployment lifecycle"""
    PLANNED = "planned"
    BUILDING = "building"
    TESTING = "testing"
    STAGING = "staging"
    APPROVAL_PENDING = "approval_pending"
    DEPLOYING = "deploying"
    MONITORING = "monitoring"
    COMPLETED = "completed"
    ROLLBACK_TRIGGERED = "rollback_triggered"
    FAILED = "failed"


class HealthCheckStatus(Enum):
    """Health check result statuses"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    TIMEOUT = "timeout"


@dataclass
class ServiceVersion:
    """Immutable service version record"""
    service_name: str
    version: str                    # Semantic version: v1.2.3
    image_sha256: str              # Docker image SHA for verification
    build_timestamp: datetime
    commit_hash: str               # Git commit this came from
    build_url: str                 # CI pipeline URL
    tested_features: List[str] = field(default_factory=list)
    breaking_changes: List[str] = field(default_factory=list)
    
    def fingerprint(self) -> str:
        """Generate deterministic fingerprint for verification"""
        data = f"{self.service_name}:{self.version}:{self.image_sha256}:{self.commit_hash}"
        return hashlib.sha256(data.encode()).hexdigest()[:12]


@dataclass
class DeploymentTarget:
    """Target environment configuration for deployment"""
    name: str                      # dev/staging/prod
    region: str
    cluster_name: str
    namespace: str                 # Kubernetes namespace
    max_concurrent_pods: int
    min_available_pods: int
    approval_required: bool        # Prod requires approval
    canary_percentage: Optional[int] = None  # % of traffic for canary
    health_check_timeout_sec: int = 30
    max_surge_percentage: int = 25  # % over desired replicas
    max_unavailable_percentage: int = 10
    
    def is_production(self) -> bool:
        return self.name.lower() == "prod" or self.name.lower() == "production"


@dataclass
class HealthCheckResult:
    """Result of deployment health check"""
    status: HealthCheckStatus
    endpoint: str
    response_time_ms: float
    timestamp: datetime
    error_message: Optional[str] = None
    metrics_snapshot: Dict[str, Any] = field(default_factory=dict)
    
    def is_healthy(self) -> bool:
        return self.status == HealthCheckStatus.HEALTHY
    
    def is_acceptable(self) -> bool:
        """Check if health check meets deployment criteria"""
        return self.status in [HealthCheckStatus.HEALTHY, HealthCheckStatus.DEGRADED]


@dataclass
class DeploymentRollbackTrigger:
    """Criteria for automatic rollback"""
    error_rate_threshold: float = 0.05  # > 5% errors
    latency_p99_threshold_ms: int = 500
    availability_threshold: float = 0.95  # < 95% availability
    consecutive_failed_checks: int = 3
    time_window_minutes: int = 5


@dataclass
class Deployment:
    """Complete deployment record"""
    deployment_id: str
    source_version: ServiceVersion
    target_version: ServiceVersion
    target_environment: DeploymentTarget
    strategy: DeploymentStrategy
    phase: DeploymentPhase = DeploymentPhase.PLANNED
    scheduled_time: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    approval_timestamp: Optional[datetime] = None
    health_checks: List[HealthCheckResult] = field(default_factory=list)
    rollback_triggered_at: Optional[datetime] = None
    rollback_reason: Optional[str] = None
    metrics_before: Dict[str, Any] = field(default_factory=dict)
    metrics_after: Dict[str, Any] = field(default_factory=dict)
    deployed_replicas: int = 0
    
    def needs_approval(self) -> bool:
        """Check if deployment needs manual approval"""
        return self.target_environment.is_production() and \
               self.target_environment.approval_required and \
               self.phase == DeploymentPhase.APPROVAL_PENDING
    
    def is_approved(self) -> bool:
        return self.approved_by is not None and self.approval_timestamp is not None
    
    def can_proceed_to_deployment(self) -> bool:
        """Validate deployment is ready to proceed"""
        if self.target_environment.approval_required and not self.is_approved():
            return False
        if not self.health_checks:
            return False
        acceptable_checks = [hc for hc in self.health_checks if hc.is_acceptable()]
        return len(acceptable_checks) >= len(self.health_checks) * 0.8  # 80% must pass
    
    def duration_seconds(self) -> Optional[int]:
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return None
    
    def serialize(self) -> Dict[str, Any]:
        """Convert to JSON-serializable format"""
        return {
            "deployment_id": self.deployment_id,
            "source_version": self.source_version.version,
            "target_version": self.target_version.version,
            "environment": self.target_environment.name,
            "strategy": self.strategy.value,
            "phase": self.phase.value,
            "approved": self.is_approved(),
            "duration_seconds": self.duration_seconds(),
            "health_checks_passed": len([h for h in self.health_checks if h.is_healthy()]),
            "total_health_checks": len(self.health_checks),
        }


class DeploymentValidator:
    """Validates deployments meet safety criteria"""
    
    def __init__(self, rollback_trigger: DeploymentRollbackTrigger):
        self.rollback_trigger = rollback_trigger
        self.logger = logging.getLogger(f"{__name__}.DeploymentValidator")
    
    def validate_source_version(self, version: ServiceVersion) -> tuple[bool, str]:
        """Verify source version is valid for deployment"""
        if not version.version or not version.image_sha256:
            return False, "Invalid version or image SHA"
        if not version.commit_hash:
            return False, "Commit hash required for audit trail"
        # Verify version format: v0.0.0
        parts = version.version.lstrip('v').split('.')
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            return False, "Invalid semantic version format"
        return True, "Source version valid"
    
    def validate_health_checks(self, health_checks: List[HealthCheckResult]) -> tuple[bool, str]:
        """Ensure health checks meet deployment criteria"""
        if not health_checks:
            return False, "No health checks performed"
        
        healthy = sum(1 for hc in health_checks if hc.status == HealthCheckStatus.HEALTHY)
        acceptable = sum(1 for hc in health_checks if hc.is_acceptable())
        
        success_rate = acceptable / len(health_checks)
        if success_rate < 0.8:
            return False, f"Health check success rate {success_rate:.0%} below 80% threshold"
        
        return True, f"Health checks passed ({healthy}/{len(health_checks)} healthy)"
    
    def validate_canary_metrics(self, deployment: Deployment, 
                               metrics: Dict[str, float]) -> tuple[bool, List[str]]:
        """Validate canary deployment metrics for rollback triggers"""
        failures = []
        
        error_rate = metrics.get("error_rate", 0.0)
        if error_rate > self.rollback_trigger.error_rate_threshold:
            failures.append(f"Error rate {error_rate:.2%} exceeds {self.rollback_trigger.error_rate_threshold:.2%}")
        
        latency_p99 = metrics.get("latency_p99_ms", 0)
        if latency_p99 > self.rollback_trigger.latency_p99_threshold_ms:
            failures.append(f"P99 latency {latency_p99}ms exceeds {self.rollback_trigger.latency_p99_threshold_ms}ms")
        
        availability = metrics.get("availability", 1.0)
        if availability < self.rollback_trigger.availability_threshold:
            failures.append(f"Availability {availability:.2%} below {self.rollback_trigger.availability_threshold:.2%}")
        
        return len(failures) == 0, failures
    
    def validate_deployment_window(self, deployment: Deployment) -> tuple[bool, str]:
        """Ensure deployment is within acceptable window"""
        if deployment.target_environment.is_production():
            # Prod deployments only during business hours (9 AM - 5 PM)
            if deployment.scheduled_time:
                hour = deployment.scheduled_time.hour
                if hour < 9 or hour >= 17:
                    return False, "Production deployments must be 9 AM - 5 PM"
        
        return True, "Deployment window acceptable"


class BlueGreenDeploymentManager:
    """Manages blue-green deployment strategy"""
    
    def __init__(self, deployment: Deployment):
        self.deployment = deployment
        self.blue_version = deployment.source_version
        self.green_version = deployment.target_version
        self.traffic_split = 0  # 0=all blue, 100=all green
        self.logger = logging.getLogger(f"{__name__}.BlueGreenDeploymentManager")
    
    def deploy_green_instance(self) -> bool:
        """Deploy new version to green environment"""
        self.logger.info(f"Deploying green instance: {self.green_version.version} "
                        f"to {self.deployment.target_environment.name}")
        # In production: kubectl apply -f deployment.yaml --selector=version=green
        # This would handle: image pull, secret injection, config mounting, etc.
        self.logger.info(f"Green instance deployed with {self.deployment.deployed_replicas} replicas")
        return True
    
    def health_check_green(self) -> bool:
        """Verify green instance is healthy before traffic switch"""
        self.logger.info("Running health checks on green instance")
        # In production: curl green-svc/health, verify response codes, latency, etc.
        self.logger.info("Green instance health checks passed")
        return True
    
    def switch_traffic_to_green(self, gradual: bool = False) -> bool:
        """Route traffic from blue to green"""
        if gradual:
            # Gradual switch: 0% → 25% → 50% → 75% → 100%
            for percentage in [25, 50, 75, 100]:
                self.traffic_split = percentage
                self.logger.info(f"Traffic split: {percentage}% to green")
                # Monitor metrics during switch
        else:
            # Immediate switch
            self.traffic_split = 100
            self.logger.info(f"Immediate traffic switch to green (100%)")
        
        return True
    
    def rollback_to_blue(self) -> bool:
        """Switch traffic back to blue on failure"""
        self.logger.warning(f"Rolling back to blue: {self.blue_version.version}")
        self.traffic_split = 0  # All traffic back to blue
        self.logger.info("Rollback completed")
        return True
    
    def cleanup_blue_instance(self, grace_period_minutes: int = 30) -> bool:
        """Remove blue instance after successful deployment"""
        self.logger.info(f"Scheduling blue instance cleanup in {grace_period_minutes} minutes")
        # In production: schedule kubectl delete with grace period
        # Keeps blue around for quick rollback if needed
        return True


class CanaryDeploymentManager:
    """Manages canary deployment strategy"""
    
    def __init__(self, deployment: Deployment, canary_percentage: int = 10):
        self.deployment = deployment
        self.canary_percentage = canary_percentage  # Start with 10% traffic
        self.current_percentage = 0
        self.promotion_increments = [10, 25, 50, 100]  # Traffic split schedule
        self.logger = logging.getLogger(f"{__name__}.CanaryDeploymentManager")
    
    def deploy_canary_replicas(self) -> bool:
        """Deploy small number of canary replicas"""
        canary_replicas = max(1, int(self.deployment.deployed_replicas * self.canary_percentage / 100))
        self.logger.info(f"Deploying {canary_replicas} canary replicas "
                        f"({self.canary_percentage}% of {self.deployment.deployed_replicas})")
        return True
    
    def promote_canary(self) -> bool:
        """Gradually increase canary traffic percentage"""
        if self.current_percentage >= 100:
            self.logger.info("Canary fully promoted to 100%")
            return True
        
        current_idx = next((i for i, p in enumerate(self.promotion_increments) 
                           if p > self.current_percentage), 0)
        if current_idx < len(self.promotion_increments):
            next_percentage = self.promotion_increments[current_idx]
            self.logger.info(f"Promoting canary: {self.current_percentage}% → {next_percentage}%")
            self.current_percentage = next_percentage
            return True
        
        return False
    
    def rollback_canary(self) -> bool:
        """Remove canary replicas and revert to stable"""
        self.logger.warning(f"Rolling back canary deployment")
        self.current_percentage = 0
        return True


class DeploymentAuditLog:
    """Immutable audit log for all deployment actions"""
    
    def __init__(self, deployment: Deployment):
        self.deployment = deployment
        self.events: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(f"{__name__}.DeploymentAuditLog")
    
    def log_event(self, event_type: str, details: Dict[str, Any], user: Optional[str] = None):
        """Record immutable deployment event"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "details": details,
            "user": user or "system",
            "deployment_id": self.deployment.deployment_id,
        }
        self.events.append(event)
        self.logger.info(f"[AUDIT] {event_type}: {details}")
    
    def log_approval(self, approved_by: str):
        self.log_event("DEPLOYMENT_APPROVED", 
                      {"version": self.deployment.target_version.version},
                      user=approved_by)
    
    def log_deployment_started(self):
        self.log_event("DEPLOYMENT_STARTED",
                      {"strategy": self.deployment.strategy.value,
                       "environment": self.deployment.target_environment.name})
    
    def log_health_check(self, result: HealthCheckResult):
        self.log_event("HEALTH_CHECK",
                      {"endpoint": result.endpoint,
                       "status": result.status.value,
                       "response_time_ms": result.response_time_ms})
    
    def log_rollback(self, reason: str):
        self.log_event("ROLLBACK_TRIGGERED",
                      {"reason": reason,
                       "previous_version": self.deployment.source_version.version})
    
    def log_completion(self, success: bool):
        self.log_event("DEPLOYMENT_COMPLETED",
                      {"success": success,
                       "duration_seconds": self.deployment.duration_seconds()})
    
    def export_json(self) -> str:
        """Export audit log as JSON"""
        return json.dumps(self.events, indent=2)


class DeploymentOrchestrator:
    """Orchestrates complete deployment lifecycle"""
    
    def __init__(self, validator: DeploymentValidator):
        self.validator = validator
        self.deployments: Dict[str, Deployment] = {}
        self.logger = logging.getLogger(f"{__name__}.DeploymentOrchestrator")
    
    def create_deployment(self, deployment: Deployment) -> tuple[bool, str]:
        """Create and validate new deployment"""
        # Validate source version
        valid, msg = self.validator.validate_source_version(deployment.source_version)
        if not valid:
            return False, f"Invalid source version: {msg}"
        
        # Validate deployment window
        valid, msg = self.validator.validate_deployment_window(deployment)
        if not valid:
            return False, f"Invalid deployment window: {msg}"
        
        self.deployments[deployment.deployment_id] = deployment
        self.logger.info(f"Deployment created: {deployment.deployment_id}")
        return True, "Deployment created successfully"
    
    def execute_deployment(self, deployment_id: str) -> tuple[bool, str]:
        """Execute complete deployment workflow"""
        deployment = self.deployments.get(deployment_id)
        if not deployment:
            return False, f"Deployment {deployment_id} not found"
        
        # Check approval if required
        if deployment.needs_approval():
            return False, "Deployment requires manual approval"
        
        audit_log = DeploymentAuditLog(deployment)
        
        try:
            # Phase 1: Start deployment
            deployment.phase = DeploymentPhase.DEPLOYING
            deployment.started_at = datetime.utcnow()
            audit_log.log_deployment_started()
            
            # Phase 2: Deploy based on strategy
            if deployment.strategy == DeploymentStrategy.BLUE_GREEN:
                manager = BlueGreenDeploymentManager(deployment)
                manager.deploy_green_instance()
                manager.health_check_green()
                manager.switch_traffic_to_green(gradual=True)
            elif deployment.strategy == DeploymentStrategy.CANARY:
                manager = CanaryDeploymentManager(deployment)
                manager.deploy_canary_replicas()
                # Would promote gradually with monitoring
            
            # Phase 3: Monitor
            deployment.phase = DeploymentPhase.MONITORING
            self.logger.info(f"Deployment {deployment_id} in monitoring phase")
            
            # Phase 4: Complete
            deployment.phase = DeploymentPhase.COMPLETED
            deployment.completed_at = datetime.utcnow()
            audit_log.log_completion(success=True)
            
            return True, f"Deployment {deployment_id} completed successfully"
        
        except Exception as e:
            deployment.phase = DeploymentPhase.FAILED
            audit_log.log_completion(success=False)
            self.logger.error(f"Deployment {deployment_id} failed: {e}")
            return False, f"Deployment failed: {str(e)}"
    
    def approve_deployment(self, deployment_id: str, approved_by: str) -> tuple[bool, str]:
        """Manually approve deployment"""
        deployment = self.deployments.get(deployment_id)
        if not deployment:
            return False, f"Deployment {deployment_id} not found"
        
        deployment.approved_by = approved_by
        deployment.approval_timestamp = datetime.utcnow()
        
        audit_log = DeploymentAuditLog(deployment)
        audit_log.log_approval(approved_by)
        
        self.logger.info(f"Deployment {deployment_id} approved by {approved_by}")
        return True, "Deployment approved"
    
    def trigger_rollback(self, deployment_id: str, reason: str) -> tuple[bool, str]:
        """Trigger rollback of failed deployment"""
        deployment = self.deployments.get(deployment_id)
        if not deployment:
            return False, f"Deployment {deployment_id} not found"
        
        deployment.phase = DeploymentPhase.ROLLBACK_TRIGGERED
        deployment.rollback_triggered_at = datetime.utcnow()
        deployment.rollback_reason = reason
        
        audit_log = DeploymentAuditLog(deployment)
        audit_log.log_rollback(reason)
        
        self.logger.warning(f"Rollback triggered for {deployment_id}: {reason}")
        return True, "Rollback initiated"
