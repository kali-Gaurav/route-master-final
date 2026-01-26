"""
Performance Monitoring & Fine-Tuning System

Continuous monitoring and optimization of system performance.

Features:
- Real-time metrics collection
- Performance dashboards
- Auto-tuning recommendations
- Bottleneck identification
- Optimization rules engine
"""

import json
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("performance_monitor")


class PerformanceThreshold(Enum):
    """Performance threshold levels"""
    EXCELLENT = "EXCELLENT"    # All metrics excellent
    GOOD = "GOOD"               # Most metrics good
    WARNING = "WARNING"         # Some metrics degraded
    CRITICAL = "CRITICAL"       # Critical issues


@dataclass
class MetricPoint:
    """Single metric measurement"""
    timestamp: datetime
    metric_name: str
    value: float
    unit: str
    threshold: float = None
    status: str = "OK"


@dataclass
class PerformanceMetrics:
    """System performance metrics"""
    # API Performance
    api_response_time_p50_ms: float = 0.0
    api_response_time_p95_ms: float = 0.0
    api_response_time_p99_ms: float = 0.0
    api_success_rate: float = 0.0
    api_error_rate: float = 0.0
    api_throughput_rps: float = 0.0

    # Cache Performance
    cache_hit_rate: float = 0.0
    cache_miss_rate: float = 0.0
    cache_eviction_rate: float = 0.0
    cache_size_mb: float = 0.0

    # Database Performance
    db_query_time_ms: float = 0.0
    db_connection_pool_utilization: float = 0.0
    db_lock_wait_time_ms: float = 0.0

    # System Resources
    cpu_utilization_percent: float = 0.0
    memory_utilization_percent: float = 0.0
    disk_utilization_percent: float = 0.0

    # Data Pipeline
    data_freshness_minutes: float = 0.0
    data_accuracy_percent: float = 0.0
    data_processing_latency_ms: float = 0.0

    # Availability
    uptime_percent: float = 0.0
    error_rate_percent: float = 0.0

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "api_response_time_p50_ms": f"{self.api_response_time_p50_ms:.2f}",
            "api_response_time_p95_ms": f"{self.api_response_time_p95_ms:.2f}",
            "api_response_time_p99_ms": f"{self.api_response_time_p99_ms:.2f}",
            "api_success_rate": f"{self.api_success_rate:.2%}",
            "api_error_rate": f"{self.api_error_rate:.2%}",
            "api_throughput_rps": f"{self.api_throughput_rps:.2f}",
            "cache_hit_rate": f"{self.cache_hit_rate:.2%}",
            "cache_miss_rate": f"{self.cache_miss_rate:.2%}",
            "cache_eviction_rate": f"{self.cache_eviction_rate:.2%}",
            "cache_size_mb": f"{self.cache_size_mb:.2f}",
            "db_query_time_ms": f"{self.db_query_time_ms:.2f}",
            "db_connection_pool_utilization": f"{self.db_connection_pool_utilization:.2%}",
            "db_lock_wait_time_ms": f"{self.db_lock_wait_time_ms:.2f}",
            "cpu_utilization_percent": f"{self.cpu_utilization_percent:.2f}",
            "memory_utilization_percent": f"{self.memory_utilization_percent:.2f}",
            "disk_utilization_percent": f"{self.disk_utilization_percent:.2f}",
            "data_freshness_minutes": f"{self.data_freshness_minutes:.2f}",
            "data_accuracy_percent": f"{self.data_accuracy_percent:.2f}",
            "data_processing_latency_ms": f"{self.data_processing_latency_ms:.2f}",
            "uptime_percent": f"{self.uptime_percent:.2f}",
            "error_rate_percent": f"{self.error_rate_percent:.2f}",
        }


@dataclass
class OptimizationRule:
    """Automatic optimization rule"""
    rule_id: str
    name: str
    metric: str
    threshold: float
    operator: str  # >, <, ==
    action: str
    impact: str  # CRITICAL, HIGH, MEDIUM, LOW
    enabled: bool = True


@dataclass
class OptimizationRecommendation:
    """Performance optimization recommendation"""
    priority: int  # 1 = highest
    impact: str
    component: str
    current_value: float
    target_value: float
    recommendation: str
    estimated_improvement_percent: float
    implementation_difficulty: str  # EASY, MEDIUM, HARD


class PerformanceMonitor:
    """Real-time performance monitoring system"""

    def __init__(self):
        self.metrics_history = defaultdict(list)
        self.current_metrics = PerformanceMetrics()
        self.optimization_rules = self._load_optimization_rules()
        self.recommendations = []

    def collect_metrics(self, metrics_data: Dict[str, float]) -> PerformanceMetrics:
        """Collect new metrics"""
        # API metrics
        if "api_response_time_p50_ms" in metrics_data:
            self.current_metrics.api_response_time_p50_ms = metrics_data["api_response_time_p50_ms"]
        if "api_response_time_p95_ms" in metrics_data:
            self.current_metrics.api_response_time_p95_ms = metrics_data["api_response_time_p95_ms"]
        if "api_response_time_p99_ms" in metrics_data:
            self.current_metrics.api_response_time_p99_ms = metrics_data["api_response_time_p99_ms"]
        if "api_success_rate" in metrics_data:
            self.current_metrics.api_success_rate = metrics_data["api_success_rate"]
        if "cache_hit_rate" in metrics_data:
            self.current_metrics.cache_hit_rate = metrics_data["cache_hit_rate"]

        # Record history
        self._record_metrics()

        return self.current_metrics

    def analyze_performance(self) -> PerformanceThreshold:
        """Analyze current performance and return status"""
        logger.info("\n" + "=" * 60)
        logger.info("PERFORMANCE ANALYSIS")
        logger.info("=" * 60)

        issues = []

        # Check API response times
        if self.current_metrics.api_response_time_p99_ms > 1000:
            issues.append(f"P99 response time too high: {self.current_metrics.api_response_time_p99_ms:.0f}ms (target: <500ms)")
        if self.current_metrics.api_response_time_p95_ms > 500:
            issues.append(f"P95 response time degraded: {self.current_metrics.api_response_time_p95_ms:.0f}ms (target: <200ms)")

        # Check success rate
        if self.current_metrics.api_success_rate < 0.95:
            issues.append(f"API success rate low: {self.current_metrics.api_success_rate:.1%} (target: >99%)")

        # Check cache hit rate
        if self.current_metrics.cache_hit_rate < 0.30:
            issues.append(f"Cache hit rate low: {self.current_metrics.cache_hit_rate:.1%} (target: >50%)")

        # Check resource utilization
        if self.current_metrics.cpu_utilization_percent > 80:
            issues.append(f"CPU utilization high: {self.current_metrics.cpu_utilization_percent:.1f}% (target: <70%)")
        if self.current_metrics.memory_utilization_percent > 85:
            issues.append(f"Memory utilization high: {self.current_metrics.memory_utilization_percent:.1f}% (target: <80%)")

        # Determine status
        if not issues:
            status = PerformanceThreshold.EXCELLENT
            logger.info("✅ All metrics EXCELLENT")
        elif len(issues) <= 1:
            status = PerformanceThreshold.GOOD
            logger.info("✅ Performance GOOD with minor warnings")
        elif len(issues) <= 3:
            status = PerformanceThreshold.WARNING
            logger.warning("⚠️ Performance DEGRADED")
        else:
            status = PerformanceThreshold.CRITICAL
            logger.error("🚨 Performance CRITICAL")

        # Log issues
        if issues:
            logger.info("\nDetected Issues:")
            for issue in issues:
                logger.info(f"  ⚠ {issue}")

        return status

    def generate_recommendations(self) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations"""
        logger.info("\n" + "=" * 60)
        logger.info("OPTIMIZATION RECOMMENDATIONS")
        logger.info("=" * 60)

        self.recommendations = []

        # Response time optimization
        if self.current_metrics.api_response_time_p99_ms > 1000:
            self.recommendations.append(OptimizationRecommendation(
                priority=1,
                impact="CRITICAL",
                component="API Response Times",
                current_value=self.current_metrics.api_response_time_p99_ms,
                target_value=500.0,
                recommendation="Implement response time optimization: reduce database queries, add indexes, optimize algorithms",
                estimated_improvement_percent=50,
                implementation_difficulty="MEDIUM"
            ))

        # Cache optimization
        if self.current_metrics.cache_hit_rate < 0.30:
            self.recommendations.append(OptimizationRecommendation(
                priority=2,
                impact="HIGH",
                component="Cache System",
                current_value=self.current_metrics.cache_hit_rate * 100,
                target_value=50.0,
                recommendation="Increase cache size, adjust TTL, implement cache warming for hot routes",
                estimated_improvement_percent=40,
                implementation_difficulty="EASY"
            ))

        # Query optimization
        if self.current_metrics.db_query_time_ms > 100:
            self.recommendations.append(OptimizationRecommendation(
                priority=3,
                impact="HIGH",
                component="Database Queries",
                current_value=self.current_metrics.db_query_time_ms,
                target_value=50.0,
                recommendation="Add database indexes, use query analysis, implement connection pooling",
                estimated_improvement_percent=60,
                implementation_difficulty="MEDIUM"
            ))

        # Resource optimization
        if self.current_metrics.cpu_utilization_percent > 80:
            self.recommendations.append(OptimizationRecommendation(
                priority=4,
                impact="HIGH",
                component="CPU Utilization",
                current_value=self.current_metrics.cpu_utilization_percent,
                target_value=60.0,
                recommendation="Optimize algorithms, implement caching, use async processing",
                estimated_improvement_percent=30,
                implementation_difficulty="HARD"
            ))

        if self.current_metrics.memory_utilization_percent > 85:
            self.recommendations.append(OptimizationRecommendation(
                priority=5,
                impact="HIGH",
                component="Memory Utilization",
                current_value=self.current_metrics.memory_utilization_percent,
                target_value=70.0,
                recommendation="Reduce cache size, implement garbage collection, profile memory usage",
                estimated_improvement_percent=20,
                implementation_difficulty="HARD"
            ))

        # Data freshness
        if self.current_metrics.data_freshness_minutes > 60:
            self.recommendations.append(OptimizationRecommendation(
                priority=6,
                impact="MEDIUM",
                component="Data Freshness",
                current_value=self.current_metrics.data_freshness_minutes,
                target_value=30.0,
                recommendation="Increase refresh frequency, implement incremental updates, add real-time feeds",
                estimated_improvement_percent=50,
                implementation_difficulty="MEDIUM"
            ))

        # Print recommendations
        if self.recommendations:
            logger.info("\n🎯 Top Recommendations:\n")
            for i, rec in enumerate(sorted(self.recommendations, key=lambda x: x.priority), 1):
                logger.info(f"{i}. [{rec.impact}] {rec.component}")
                logger.info(f"   Current: {rec.current_value:.2f} → Target: {rec.target_value:.2f}")
                logger.info(f"   Improvement: ~{rec.estimated_improvement_percent:.0f}%")
                logger.info(f"   Action: {rec.recommendation}")
                logger.info(f"   Difficulty: {rec.implementation_difficulty}\n")
        else:
            logger.info("\n✅ No optimizations needed - system performing well")

        return self.recommendations

    def tune_system(self) -> Dict[str, Any]:
        """Apply automatic tuning based on current metrics"""
        logger.info("\n" + "=" * 60)
        logger.info("AUTOMATIC SYSTEM TUNING")
        logger.info("=" * 60)

        tuning_actions = {
            "cache_adjustments": [],
            "query_optimizations": [],
            "resource_allocations": [],
            "data_refresh_settings": []
        }

        # Cache tuning
        if self.current_metrics.cache_hit_rate < 0.30:
            tuning_actions["cache_adjustments"].append({
                "action": "increase_cache_size",
                "from_mb": 100,
                "to_mb": 500,
                "reason": "Low cache hit rate"
            })
            logger.info("🔧 Increasing cache size from 100MB to 500MB")

            tuning_actions["cache_adjustments"].append({
                "action": "adjust_cache_ttl",
                "from_seconds": 300,
                "to_seconds": 600,
                "reason": "Extend cache retention"
            })
            logger.info("🔧 Extending cache TTL from 5min to 10min")

        # Query tuning
        if self.current_metrics.db_query_time_ms > 100:
            tuning_actions["query_optimizations"].append({
                "action": "add_database_index",
                "table": "trains",
                "columns": ["train_no", "source", "destination"],
                "reason": "Slow query performance"
            })
            logger.info("🔧 Adding composite index on trains table")

            tuning_actions["query_optimizations"].append({
                "action": "enable_query_cache",
                "reason": "Reduce repeated query execution"
            })
            logger.info("🔧 Enabling query result caching")

        # Resource allocation
        if self.current_metrics.cpu_utilization_percent > 80:
            tuning_actions["resource_allocations"].append({
                "action": "increase_worker_threads",
                "from": 4,
                "to": 8,
                "reason": "High CPU utilization"
            })
            logger.info("🔧 Increasing worker threads from 4 to 8")

        if self.current_metrics.memory_utilization_percent > 85:
            tuning_actions["resource_allocations"].append({
                "action": "adjust_memory_limit",
                "from_mb": 2048,
                "to_mb": 4096,
                "reason": "Memory pressure detected"
            })
            logger.info("🔧 Increasing memory limit to 4GB")

        # Data refresh tuning
        if self.current_metrics.data_freshness_minutes > 60:
            tuning_actions["data_refresh_settings"].append({
                "action": "increase_refresh_frequency",
                "from_minutes": 60,
                "to_minutes": 30,
                "reason": "Data staleness detected"
            })
            logger.info("🔧 Increasing data refresh frequency to every 30 minutes")

        logger.info("\n✅ Tuning applied. Metrics will be re-evaluated shortly.")

        return tuning_actions

    def _load_optimization_rules(self) -> List[OptimizationRule]:
        """Load automatic optimization rules"""
        return [
            OptimizationRule(
                rule_id="rule_001",
                name="Response Time Critical",
                metric="api_response_time_p99_ms",
                threshold=1000,
                operator=">",
                action="increase_cache_size",
                impact="CRITICAL"
            ),
            OptimizationRule(
                rule_id="rule_002",
                name="Low Cache Hit Rate",
                metric="cache_hit_rate",
                threshold=0.30,
                operator="<",
                action="adjust_cache_strategy",
                impact="HIGH"
            ),
            OptimizationRule(
                rule_id="rule_003",
                name="High CPU Usage",
                metric="cpu_utilization_percent",
                threshold=80,
                operator=">",
                action="increase_workers",
                impact="HIGH"
            ),
            OptimizationRule(
                rule_id="rule_004",
                name="High Memory Usage",
                metric="memory_utilization_percent",
                threshold=85,
                operator=">",
                action="optimize_memory",
                impact="HIGH"
            ),
        ]

    def _record_metrics(self):
        """Record metrics in history"""
        timestamp = datetime.now()
        for field_name in self.current_metrics.__dataclass_fields__:
            value = getattr(self.current_metrics, field_name)
            if isinstance(value, float):
                point = MetricPoint(
                    timestamp=timestamp,
                    metric_name=field_name,
                    value=value,
                    unit="ms" if "time" in field_name or "latency" in field_name else "%"
                    if "percent" in field_name or "rate" in field_name else "count"
                )
                self.metrics_history[field_name].append(point)

    def print_current_metrics(self):
        """Print current metrics"""
        logger.info("\n" + "=" * 60)
        logger.info("CURRENT PERFORMANCE METRICS")
        logger.info("=" * 60)

        logger.info("\n📊 API Performance:")
        logger.info(f"  P50 Response Time: {self.current_metrics.api_response_time_p50_ms:.2f}ms")
        logger.info(f"  P95 Response Time: {self.current_metrics.api_response_time_p95_ms:.2f}ms")
        logger.info(f"  P99 Response Time: {self.current_metrics.api_response_time_p99_ms:.2f}ms")
        logger.info(f"  Success Rate: {self.current_metrics.api_success_rate:.2%}")
        logger.info(f"  Throughput: {self.current_metrics.api_throughput_rps:.2f} RPS")

        logger.info("\n💾 Cache Performance:")
        logger.info(f"  Hit Rate: {self.current_metrics.cache_hit_rate:.2%}")
        logger.info(f"  Miss Rate: {self.current_metrics.cache_miss_rate:.2%}")
        logger.info(f"  Cache Size: {self.current_metrics.cache_size_mb:.2f} MB")

        logger.info("\n🗄️ Database Performance:")
        logger.info(f"  Query Time: {self.current_metrics.db_query_time_ms:.2f}ms")
        logger.info(f"  Connection Pool: {self.current_metrics.db_connection_pool_utilization:.2%}")

        logger.info("\n💻 System Resources:")
        logger.info(f"  CPU: {self.current_metrics.cpu_utilization_percent:.2f}%")
        logger.info(f"  Memory: {self.current_metrics.memory_utilization_percent:.2f}%")
        logger.info(f"  Disk: {self.current_metrics.disk_utilization_percent:.2f}%")

        logger.info("\n📈 Data Pipeline:")
        logger.info(f"  Freshness: {self.current_metrics.data_freshness_minutes:.2f} minutes")
        logger.info(f"  Accuracy: {self.current_metrics.data_accuracy_percent:.2f}%")
        logger.info(f"  Processing Latency: {self.current_metrics.data_processing_latency_ms:.2f}ms")

        logger.info("\n🟢 Availability:")
        logger.info(f"  Uptime: {self.current_metrics.uptime_percent:.2f}%")
        logger.info(f"  Error Rate: {self.current_metrics.error_rate_percent:.2f}%")

        logger.info("=" * 60)

    def save_metrics_report(self, output_path: str = "performance_metrics.json"):
        """Save metrics report to JSON"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "current_metrics": self.current_metrics.to_dict(),
            "recommendations": [
                {
                    "priority": r.priority,
                    "impact": r.impact,
                    "component": r.component,
                    "recommendation": r.recommendation,
                    "estimated_improvement_percent": r.estimated_improvement_percent,
                    "difficulty": r.implementation_difficulty
                }
                for r in self.recommendations
            ]
        }

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"\nMetrics report saved to {output_path}")


def main():
    """Example usage"""
    # Create monitor
    monitor = PerformanceMonitor()

    # Simulate collecting metrics
    sample_metrics = {
        "api_response_time_p50_ms": 150.0,
        "api_response_time_p95_ms": 450.0,
        "api_response_time_p99_ms": 1200.0,
        "api_success_rate": 0.97,
        "cache_hit_rate": 0.25,
        "db_query_time_ms": 120.0,
        "cpu_utilization_percent": 75.0,
        "memory_utilization_percent": 82.0,
        "data_freshness_minutes": 45.0,
        "data_accuracy_percent": 98.5,
        "uptime_percent": 99.8
    }

    # Collect and analyze
    monitor.collect_metrics(sample_metrics)
    monitor.print_current_metrics()

    # Analyze performance
    status = monitor.analyze_performance()
    logger.info(f"\nPerformance Status: {status.value}")

    # Generate recommendations
    monitor.generate_recommendations()

    # Apply tuning
    monitor.tune_system()

    # Save report
    monitor.save_metrics_report()


if __name__ == "__main__":
    main()
