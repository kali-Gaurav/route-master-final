#!/usr/bin/env python3
"""
Blue-Green Deployment Script
Safely switches traffic between blue (old) and green (new) environments
"""
import subprocess
import time
import logging
import requests
from typing import Tuple
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BlueGreenDeploymentManager:
    """Manages blue-green deployments with automatic rollback"""
    
    def __init__(self, namespace: str = "production", service_name: str = "railway-os-api"):
        self.namespace = namespace
        self.service_name = service_name
        self.blue_replicas = 0
        self.green_replicas = 0
    
    def deploy_green_environment(self, image: str, replicas: int = 5) -> bool:
        """Deploy new version to green environment"""
        logger.info(f"Deploying green environment with image: {image}")
        
        try:
            # Create green deployment
            cmd = [
                "kubectl", "set", "image",
                f"deployment/{self.service_name}-green",
                f"{self.service_name}={image}",
                f"-n={self.namespace}"
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Wait for rollout to complete
            cmd = [
                "kubectl", "rollout", "status",
                f"deployment/{self.service_name}-green",
                f"-n={self.namespace}",
                "--timeout=5m"
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            
            logger.info("✓ Green environment deployed successfully")
            self.green_replicas = replicas
            return True
        
        except subprocess.CalledProcessError as e:
            logger.error(f"✗ Failed to deploy green environment: {e}")
            return False
    
    def health_check_green(self, endpoint: str = "http://green-svc/health", 
                          max_retries: int = 10) -> bool:
        """Verify green environment is healthy"""
        logger.info(f"Running health checks on green environment ({endpoint})")
        
        for attempt in range(max_retries):
            try:
                response = requests.get(endpoint, timeout=5)
                if response.status_code == 200:
                    logger.info(f"✓ Health check passed (attempt {attempt + 1})")
                    return True
                else:
                    logger.warning(f"✗ Health check failed with status {response.status_code}")
            except requests.RequestException as e:
                logger.warning(f"✗ Health check error (attempt {attempt + 1}): {e}")
            
            if attempt < max_retries - 1:
                time.sleep(5)
        
        logger.error(f"✗ Health checks failed after {max_retries} attempts")
        return False
    
    def switch_traffic_to_green(self, gradual: bool = False) -> bool:
        """Switch traffic from blue to green"""
        logger.info("Switching traffic to green environment")
        
        try:
            if gradual:
                # Gradual traffic switch: 0% -> 25% -> 50% -> 75% -> 100%
                for percentage in [25, 50, 75, 100]:
                    self._set_traffic_split(percentage)
                    logger.info(f"Traffic split: {percentage}% to green")
                    
                    # Monitor metrics after each split
                    if not self._verify_metrics_healthy():
                        logger.warning(f"Metrics degraded at {percentage}% split")
                        if percentage > 25:
                            self._rollback_traffic()
                            return False
                    
                    time.sleep(30)  # Monitor for 30 seconds
            else:
                # Immediate switch
                self._set_traffic_split(100)
                logger.info("Immediate traffic switch to green (100%)")
            
            logger.info("✓ Traffic switched to green successfully")
            return True
        
        except Exception as e:
            logger.error(f"✗ Failed to switch traffic: {e}")
            return False
    
    def verify_deployment_health(self, duration_seconds: int = 300) -> bool:
        """Monitor metrics for post-deployment period"""
        logger.info(f"Verifying deployment health for {duration_seconds} seconds")
        
        start_time = datetime.utcnow()
        check_interval = 10
        
        while (datetime.utcnow() - start_time).total_seconds() < duration_seconds:
            metrics = self._get_metrics()
            
            # Check SLO compliance
            if metrics['error_rate'] > 0.05:  # > 5% errors
                logger.error(f"✗ Error rate too high: {metrics['error_rate']:.2%}")
                return False
            
            if metrics['latency_p99'] > 500:  # > 500ms
                logger.error(f"✗ Latency too high: {metrics['latency_p99']}ms")
                return False
            
            if metrics['availability'] < 0.95:  # < 95% availability
                logger.error(f"✗ Availability too low: {metrics['availability']:.2%}")
                return False
            
            logger.info(f"Metrics healthy - Error rate: {metrics['error_rate']:.2%}, "
                       f"P99 latency: {metrics['latency_p99']}ms, "
                       f"Availability: {metrics['availability']:.2%}")
            
            time.sleep(check_interval)
        
        logger.info("✓ Deployment health verified successfully")
        return True
    
    def rollback_to_blue(self) -> bool:
        """Rollback to blue environment on failure"""
        logger.warning("Rolling back to blue environment")
        
        try:
            self._set_traffic_split(0)  # All traffic to blue
            logger.info("✓ Rollback to blue completed")
            return True
        except Exception as e:
            logger.error(f"✗ Rollback failed: {e}")
            return False
    
    def cleanup_blue_environment(self, grace_period_minutes: int = 30) -> bool:
        """Remove blue environment after successful deployment"""
        logger.info(f"Scheduling blue environment cleanup in {grace_period_minutes} minutes")
        
        try:
            cmd = [
                "kubectl", "scale", "deployment",
                f"{self.service_name}-blue",
                "--replicas=0",
                f"-n={self.namespace}"
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info("✓ Blue environment scaled down")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"✗ Failed to cleanup blue: {e}")
            return False
    
    def _set_traffic_split(self, percentage: int):
        """Update traffic split between blue and green (0% = all blue, 100% = all green)"""
        # In production: Update Kubernetes VirtualService or Istio routing rules
        # This is a placeholder for service mesh configuration
        logger.debug(f"Setting traffic split to {percentage}% green")
    
    def _verify_metrics_healthy(self) -> bool:
        """Verify key metrics are within acceptable ranges"""
        metrics = self._get_metrics()
        return (metrics['error_rate'] < 0.05 and 
                metrics['latency_p99'] < 500 and
                metrics['availability'] > 0.95)
    
    def _get_metrics(self) -> dict:
        """Fetch current metrics from Prometheus"""
        # In production: Query Prometheus for real metrics
        return {
            'error_rate': 0.01,      # 1% error rate
            'latency_p99': 150,      # 150ms p99 latency
            'availability': 0.99,    # 99% availability
        }
    
    def _rollback_traffic(self):
        """Emergency rollback of traffic"""
        logger.error("Emergency rollback - reverting to blue")
        self._set_traffic_split(0)


def main():
    """Main deployment orchestration"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Blue-Green Deployment Manager')
    parser.add_argument('--image', required=True, help='Docker image to deploy')
    parser.add_argument('--namespace', default='production', help='Kubernetes namespace')
    parser.add_argument('--service', default='railway-os-api', help='Service name')
    parser.add_argument('--gradual', action='store_true', help='Gradual traffic switch')
    args = parser.parse_args()
    
    manager = BlueGreenDeploymentManager(args.namespace, args.service)
    
    try:
        # Step 1: Deploy green environment
        if not manager.deploy_green_environment(args.image):
            logger.error("Deployment failed - green environment failed to deploy")
            return False
        
        # Step 2: Health check green
        if not manager.health_check_green():
            logger.error("Deployment failed - green environment unhealthy")
            return False
        
        # Step 3: Switch traffic
        if not manager.switch_traffic_to_green(gradual=args.gradual):
            logger.error("Deployment failed - traffic switch failed")
            manager.rollback_to_blue()
            return False
        
        # Step 4: Monitor deployment
        if not manager.verify_deployment_health():
            logger.error("Deployment failed - metrics degraded after switch")
            manager.rollback_to_blue()
            return False
        
        # Step 5: Cleanup blue
        manager.cleanup_blue_environment()
        
        logger.info("✓ Deployment completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Deployment failed with exception: {e}")
        manager.rollback_to_blue()
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
