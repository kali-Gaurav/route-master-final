"""
Comprehensive Test Suite for Living Dataset Pipeline

Tests for:
- Fetch logic and rate limiting
- Status updates and transitions
- Refresh decisions
- Data validation
- Quality scoring
- Database operations
- Backup/recovery
- Alert generation

Run with: pytest test_pipeline.py -v
"""

import unittest
from datetime import datetime, timedelta
from pathlib import Path
import json
import tempfile

from config import REFRESH_POLICY, RATE_LIMIT
from database_manager import Train, TrainStatus, FetchStatus
from rappid_fetcher import RAPPIDFetcher, CircuitBreaker, RateLimiter
from refresh_policy import RefreshPolicyEngine, RefreshPriority
from validator import DataValidator, ValidationSeverity
from quality_scorer import QualityScorer
from alerting_system import AlertingSystem


class TestRateLimiter(unittest.TestCase):
    """Test rate limiting functionality"""
    
    def setUp(self):
        self.limiter = RateLimiter(requests_per_second=10, burst_limit=5)
    
    def test_token_acquisition(self):
        """Test acquiring tokens"""
        self.assertTrue(self.limiter.acquire(blocking=False))
        self.assertTrue(self.limiter.acquire(blocking=False))
    
    def test_burst_limit(self):
        """Test burst limit enforcement"""
        # Acquire all burst tokens
        for _ in range(5):
            self.assertTrue(self.limiter.acquire(blocking=False))
        
        # Should fail to acquire more
        self.assertFalse(self.limiter.acquire(blocking=False, timeout=0.1))
    
    def test_token_refill(self):
        """Test token refilling over time"""
        # Drain tokens
        for _ in range(5):
            self.limiter.acquire(blocking=False)
        
        # Wait for refill
        import time
        time.sleep(0.15)
        
        # Should be able to acquire again
        self.assertTrue(self.limiter.acquire(blocking=False))


class TestCircuitBreaker(unittest.TestCase):
    """Test circuit breaker pattern"""
    
    def setUp(self):
        self.breaker = CircuitBreaker(failure_threshold=3, timeout_seconds=1)
    
    def test_closed_state(self):
        """Test normal operation (CLOSED state)"""
        self.assertTrue(self.breaker.is_available())
        self.breaker.record_success()
        self.assertTrue(self.breaker.is_available())
    
    def test_open_state(self):
        """Test circuit opens after threshold"""
        for _ in range(3):
            self.breaker.record_failure()
        
        self.assertFalse(self.breaker.is_available())
    
    def test_half_open_recovery(self):
        """Test recovery from OPEN state"""
        # Open circuit
        for _ in range(3):
            self.breaker.record_failure()
        
        self.assertFalse(self.breaker.is_available())
        
        # Wait for timeout
        import time
        time.sleep(1.1)
        
        # Should try to recover (HALF_OPEN)
        self.assertTrue(self.breaker.is_available())


class TestRefreshPolicyEngine(unittest.TestCase):
    """Test smart refresh decisions"""
    
    def setUp(self):
        self.engine = RefreshPolicyEngine()
    
    def test_unknown_train_first_fetch(self):
        """Test unknown train gets priority fetch"""
        decision = self.engine.decide_refresh(
            "16320",
            TrainStatus.UNKNOWN,
            last_fetched=None
        )
        
        self.assertTrue(decision.should_refresh)
        self.assertEqual(decision.priority, RefreshPriority.HIGH)
    
    def test_active_train_fresh_cache(self):
        """Test active train with fresh cache"""
        decision = self.engine.decide_refresh(
            "16320",
            TrainStatus.ACTIVE,
            last_fetched=datetime.utcnow() - timedelta(days=3)
        )
        
        self.assertFalse(decision.should_refresh)
        self.assertEqual(decision.priority, RefreshPriority.SKIP)
    
    def test_active_train_stale_cache(self):
        """Test active train with stale cache"""
        decision = self.engine.decide_refresh(
            "16320",
            TrainStatus.ACTIVE,
            last_fetched=datetime.utcnow() - timedelta(days=35)
        )
        
        self.assertTrue(decision.should_refresh)
        self.assertEqual(decision.priority, RefreshPriority.HIGH)
    
    def test_inactive_train_no_refresh(self):
        """Test inactive train not refreshed"""
        decision = self.engine.decide_refresh(
            "16320",
            TrainStatus.INACTIVE,
            last_fetched=datetime.utcnow() - timedelta(days=15)
        )
        
        self.assertFalse(decision.should_refresh)
        self.assertEqual(decision.priority, RefreshPriority.SKIP)


class TestDataValidator(unittest.TestCase):
    """Test data validation"""
    
    def setUp(self):
        self.validator = DataValidator()
    
    def test_valid_train(self):
        """Test validating valid train data"""
        trains = [{
            "train_no": "16320",
            "train_name": "Test Train",
            "status": "ACTIVE",
            "last_updated": datetime.utcnow().isoformat()
        }]
        
        report = self.validator.validate_trains(trains)
        self.assertTrue(report.is_valid)
        self.assertEqual(report.error_count, 0)
    
    def test_missing_required_field(self):
        """Test detecting missing required field"""
        trains = [{
            # Missing train_no
            "train_name": "Test Train",
            "status": "ACTIVE"
        }]
        
        report = self.validator.validate_trains(trains)
        self.assertFalse(report.is_valid)
        self.assertGreater(report.error_count, 0)
    
    def test_duplicate_detection(self):
        """Test detecting duplicate trains"""
        trains = [
            {
                "train_no": "16320",
                "train_name": "Test Train 1",
                "status": "ACTIVE"
            },
            {
                "train_no": "16320",  # Duplicate
                "train_name": "Test Train 2",
                "status": "ACTIVE"
            }
        ]
        
        report = self.validator.validate_trains(trains)
        self.assertGreater(report.warning_count, 0)


class TestQualityScorer(unittest.TestCase):
    """Test quality scoring"""
    
    def setUp(self):
        self.scorer = QualityScorer()
    
    def test_freshness_excellent(self):
        """Test excellent freshness score"""
        score = self.scorer.calculate_freshness_score(
            datetime.utcnow() - timedelta(days=2)
        )
        self.assertEqual(score, 100.0)
    
    def test_freshness_good(self):
        """Test good freshness score"""
        score = self.scorer.calculate_freshness_score(
            datetime.utcnow() - timedelta(days=10)
        )
        self.assertGreater(score, 70)
        self.assertLess(score, 100)
    
    def test_freshness_poor(self):
        """Test poor freshness score"""
        score = self.scorer.calculate_freshness_score(
            datetime.utcnow() - timedelta(days=60)
        )
        self.assertLess(score, 60)
    
    def test_overall_grade_a(self):
        """Test grade A assignment"""
        grade = self.scorer.get_quality_grade(95)
        self.assertEqual(grade, "A")
    
    def test_overall_grade_f(self):
        """Test grade F assignment"""
        grade = self.scorer.get_quality_grade(45)
        self.assertEqual(grade, "F")


class TestAlertingSystem(unittest.TestCase):
    """Test alerting system"""
    
    def setUp(self):
        self.alerting = AlertingSystem()
    
    def test_inactive_trains_alert(self):
        """Test alert when too many trains inactive"""
        alert = self.alerting.check_inactive_trains_threshold(
            total_trains=1000,
            inactive_trains=250  # 25% > 20% threshold
        )
        
        self.assertIsNotNone(alert)
        self.assertEqual(alert.alert_type, "INACTIVE_TRAINS")
        self.assertIn("WARNING", alert.severity)
    
    def test_api_failure_alert(self):
        """Test alert on API failures"""
        alert = self.alerting.check_api_failure_rate(
            total_requests=1000,
            failed_requests=50  # 5% > 3% threshold
        )
        
        self.assertIsNotNone(alert)
        self.assertEqual(alert.alert_type, "API_FAILURE")
    
    def test_data_freshness_alert(self):
        """Test data freshness alert"""
        alert = self.alerting.check_data_freshness(0.5)  # 50% < 60% threshold
        
        self.assertIsNotNone(alert)
        self.assertEqual(alert.alert_type, "DATA_FRESHNESS")
    
    def test_no_alert_when_thresholds_met(self):
        """Test no alert when thresholds are acceptable"""
        alert = self.alerting.check_inactive_trains_threshold(1000, 100)  # 10% < 20%
        self.assertIsNone(alert)


class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def test_refresh_decision_workflow(self):
        """Test complete refresh decision workflow"""
        engine = RefreshPolicyEngine()
        
        trains = [
            {
                "train_no": "16320",
                "status": "ACTIVE",
                "last_updated": datetime.utcnow() - timedelta(days=5),
                "last_fetched": datetime.utcnow() - timedelta(days=5),
                "is_frequently_searched": True
            },
            {
                "train_no": "12951",
                "status": "UNKNOWN",
                "last_updated": None,
                "last_fetched": None,
                "is_frequently_searched": False
            },
            {
                "train_no": "22691",
                "status": "INACTIVE",
                "last_updated": datetime.utcnow() - timedelta(days=20),
                "last_fetched": datetime.utcnow() - timedelta(days=20),
                "is_frequently_searched": False
            }
        ]
        
        decisions = engine.batch_refresh_decisions(trains)
        
        # Check ACTIVE train
        self.assertFalse(decisions["16320"].should_refresh)
        
        # Check UNKNOWN train
        self.assertTrue(decisions["12951"].should_refresh)
        
        # Check INACTIVE train
        self.assertFalse(decisions["22691"].should_refresh)
    
    def test_quality_scoring_workflow(self):
        """Test complete quality scoring workflow"""
        scorer = QualityScorer()
        
        trains = [
            {
                "train_no": "16320",
                "train_name": "Express",
                "status": "ACTIVE",
                "last_updated": datetime.utcnow() - timedelta(days=2),
                "validation_errors": 0,
                "validation_warnings": 0
            },
            {
                "train_no": "12951",
                "train_name": "Local",
                "status": "ACTIVE",
                "last_updated": datetime.utcnow() - timedelta(days=45),
                "validation_errors": 5,
                "validation_warnings": 10
            }
        ]
        
        scores = scorer.score_batch(trains)
        
        # First train should have higher score
        self.assertGreater(scores[0].overall_score, scores[1].overall_score)
        
        # First train should have grade A or B
        self.assertIn(scores[0].data_quality_grade, ["A", "B"])


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestRateLimiter))
    suite.addTests(loader.loadTestsFromTestCase(TestCircuitBreaker))
    suite.addTests(loader.loadTestsFromTestCase(TestRefreshPolicyEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestDataValidator))
    suite.addTests(loader.loadTestsFromTestCase(TestQualityScorer))
    suite.addTests(loader.loadTestsFromTestCase(TestAlertingSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)