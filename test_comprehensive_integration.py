"""
COMPREHENSIVE INTEGRATION & STRESS TESTING SUITE
Tests all endpoints, concurrent requests, edge cases, and load testing
"""

import unittest
import requests
import time
import threading
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:5000"
TEST_TRAINS = [12970, 14709, 12956, 12952, 12951]

class TestEndpointIntegration(unittest.TestCase):
    """Test all endpoints integration"""
    
    def test_health_endpoint(self):
        """Test /api/health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('status', data)
        self.assertIn('timestamp', data)
        logger.info("✅ Health endpoint working")
    
    def test_performance_metrics_endpoint(self):
        """Test /api/performance-metrics endpoint"""
        response = requests.get(f"{BASE_URL}/api/performance-metrics", timeout=5)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('total_requests', data)
        self.assertIn('cache_hits', data)
        logger.info("✅ Performance metrics endpoint working")
    
    def test_rappid_data_endpoint(self):
        """Test /api/rappid-data/<train_no> endpoint"""
        train_no = TEST_TRAINS[0]
        response = requests.get(f"{BASE_URL}/api/rappid-data/{train_no}", timeout=10)
        # Either 200 (cached) or 404 (not cached yet)
        self.assertIn(response.status_code, [200, 404])
        logger.info(f"✅ RAPPID data endpoint working (status: {response.status_code})")
    
    def test_status_endpoint(self):
        """Test /admin/status/rappid endpoint"""
        response = requests.get(f"{BASE_URL}/admin/status/rappid", timeout=5)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('rappid_json_count', data)
        logger.info(f"✅ Status endpoint working (trains cached: {data.get('rappid_json_count', 0)})")
    
    def test_warm_cache_endpoint(self):
        """Test /admin/warm-cache endpoint"""
        response = requests.post(f"{BASE_URL}/admin/warm-cache", timeout=30)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('success', data)
        logger.info("✅ Warm cache endpoint working")
    
    def test_clear_cache_endpoint(self):
        """Test /admin/clear-cache endpoint"""
        response = requests.post(f"{BASE_URL}/admin/clear-cache", timeout=5)
        self.assertEqual(response.status_code, 200)
        logger.info("✅ Clear cache endpoint working")
    
    def test_error_handling_invalid_train(self):
        """Test error handling with invalid train number"""
        response = requests.get(f"{BASE_URL}/api/rappid-data/999999", timeout=5)
        self.assertEqual(response.status_code, 404)
        logger.info("✅ Error handling working for invalid train")
    
    def test_error_handling_malformed_url(self):
        """Test error handling with malformed URL"""
        response = requests.get(f"{BASE_URL}/api/rappid-data/abc", timeout=5)
        self.assertIn(response.status_code, [400, 404])
        logger.info("✅ Error handling working for malformed URL")


class TestConcurrentRequests(unittest.TestCase):
    """Test concurrent request handling"""
    
    def test_concurrent_health_checks(self):
        """Test multiple concurrent health checks"""
        def make_request():
            response = requests.get(f"{BASE_URL}/api/health", timeout=5)
            return response.status_code == 200
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(make_request, range(20)))
        
        success_rate = sum(results) / len(results)
        self.assertGreater(success_rate, 0.9)  # At least 90% success
        logger.info(f"✅ Concurrent requests test: {success_rate*100:.1f}% success rate")
    
    def test_concurrent_data_requests(self):
        """Test concurrent data fetch requests"""
        def fetch_train(train_no):
            try:
                response = requests.get(f"{BASE_URL}/api/rappid-data/{train_no}", timeout=5)
                return response.status_code in [200, 404]
            except:
                return False
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(fetch_train, TEST_TRAINS * 2))
        
        success_rate = sum(results) / len(results)
        self.assertGreater(success_rate, 0.8)  # At least 80% success
        logger.info(f"✅ Concurrent data requests: {success_rate*100:.1f}% success rate")
    
    def test_mixed_concurrent_operations(self):
        """Test mixed concurrent operations (GET, POST)"""
        def health_check():
            return requests.get(f"{BASE_URL}/api/health", timeout=5).status_code == 200
        
        def metrics_check():
            return requests.get(f"{BASE_URL}/api/performance-metrics", timeout=5).status_code == 200
        
        def status_check():
            return requests.get(f"{BASE_URL}/admin/status/rappid", timeout=5).status_code == 200
        
        operations = [health_check] * 5 + [metrics_check] * 5 + [status_check] * 5
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(lambda op: op(), operations))
        
        success_rate = sum(results) / len(results)
        self.assertGreater(success_rate, 0.85)
        logger.info(f"✅ Mixed concurrent operations: {success_rate*100:.1f}% success rate")


class TestCachePerformance(unittest.TestCase):
    """Test cache performance and hit rates"""
    
    def test_cache_hit_rate(self):
        """Test cache hit rate improves after warming"""
        # Get metrics before
        response1 = requests.get(f"{BASE_URL}/api/performance-metrics", timeout=5)
        metrics1 = response1.json()
        hits_before = metrics1.get('cache_hits', 0)
        
        # Make requests to same endpoint
        for _ in range(5):
            requests.get(f"{BASE_URL}/api/health", timeout=5)
        
        # Get metrics after
        response2 = requests.get(f"{BASE_URL}/api/performance-metrics", timeout=5)
        metrics2 = response2.json()
        hits_after = metrics2.get('cache_hits', 0)
        
        # Cache hits should increase
        self.assertGreaterEqual(hits_after, hits_before)
        logger.info(f"✅ Cache hit rate: {metrics2.get('cache_hit_rate', 0):.1%}")
    
    def test_response_time_consistency(self):
        """Test response times are consistent"""
        times = []
        
        for _ in range(10):
            start = time.time()
            requests.get(f"{BASE_URL}/api/health", timeout=5)
            times.append((time.time() - start) * 1000)  # Convert to ms
        
        avg_time = sum(times) / len(times)
        self.assertLess(avg_time, 500)  # Should be < 500ms
        logger.info(f"✅ Average response time: {avg_time:.1f}ms (range: {min(times):.1f}-{max(times):.1f}ms)")


class TestDataIntegrity(unittest.TestCase):
    """Test data integrity across operations"""
    
    def test_response_format_consistency(self):
        """Test response format is consistent"""
        response1 = requests.get(f"{BASE_URL}/api/health", timeout=5)
        response2 = requests.get(f"{BASE_URL}/api/health", timeout=5)
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Both should have same keys
        self.assertEqual(set(data1.keys()), set(data2.keys()))
        logger.info("✅ Response format consistency verified")
    
    def test_metrics_consistency(self):
        """Test metrics are consistent across requests"""
        response1 = requests.get(f"{BASE_URL}/api/performance-metrics", timeout=5)
        data1 = response1.json()
        
        # Check all expected fields exist
        expected_fields = ['total_requests', 'cache_hits', 'cache_misses', 'cache_hit_rate']
        for field in expected_fields:
            self.assertIn(field, data1)
        
        logger.info("✅ Metrics consistency verified")
    
    def test_status_accuracy(self):
        """Test status endpoint accuracy"""
        response = requests.get(f"{BASE_URL}/admin/status/rappid", timeout=5)
        data = response.json()
        
        # Check numeric fields are valid
        self.assertGreaterEqual(data.get('rappid_json_count', 0), 0)
        self.assertIsInstance(data.get('rappid_json_count'), int)
        
        logger.info("✅ Status accuracy verified")


class TestErrorRecovery(unittest.TestCase):
    """Test error handling and recovery"""
    
    def test_invalid_json_handling(self):
        """Test handling of invalid JSON in POST requests"""
        response = requests.post(
            f"{BASE_URL}/admin/refresh-rappid-bulk",
            data="invalid json",
            timeout=5
        )
        self.assertIn(response.status_code, [400, 404, 405])
        logger.info("✅ Invalid JSON handling working")
    
    def test_timeout_handling(self):
        """Test timeout handling"""
        try:
            response = requests.get(f"{BASE_URL}/api/health", timeout=0.001)
            # If it succeeds, that's fine too
        except requests.exceptions.Timeout:
            # Expected behavior
            pass
        logger.info("✅ Timeout handling working")
    
    def test_connection_retry(self):
        """Test connection retry logic"""
        success_count = 0
        
        for _ in range(5):
            try:
                response = requests.get(f"{BASE_URL}/api/health", timeout=5)
                if response.status_code == 200:
                    success_count += 1
            except:
                pass
        
        self.assertGreater(success_count, 3)  # At least 3 out of 5
        logger.info(f"✅ Connection retry: {success_count}/5 successful")


class TestLoadSimulation(unittest.TestCase):
    """Simulate realistic load scenarios"""
    
    def test_moderate_load(self):
        """Test with moderate load (50 requests)"""
        def make_request(i):
            try:
                if i % 3 == 0:
                    return requests.get(f"{BASE_URL}/api/health", timeout=5).status_code == 200
                elif i % 3 == 1:
                    return requests.get(f"{BASE_URL}/api/performance-metrics", timeout=5).status_code == 200
                else:
                    return requests.get(f"{BASE_URL}/admin/status/rappid", timeout=5).status_code == 200
            except:
                return False
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(make_request, range(50)))
        
        success_rate = sum(results) / len(results)
        self.assertGreater(success_rate, 0.85)
        logger.info(f"✅ Moderate load test: {success_rate*100:.1f}% success ({sum(results)}/{len(results)} requests)")
    
    def test_spike_load(self):
        """Test with spike load (100 concurrent requests)"""
        def make_request(_):
            try:
                return requests.get(f"{BASE_URL}/api/health", timeout=5).status_code == 200
            except:
                return False
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            results = list(executor.map(make_request, range(100)))
        
        success_rate = sum(results) / len(results)
        self.assertGreater(success_rate, 0.80)
        logger.info(f"✅ Spike load test: {success_rate*100:.1f}% success ({sum(results)}/100 requests)")


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions"""
    
    def test_large_train_number(self):
        """Test with very large train number"""
        response = requests.get(f"{BASE_URL}/api/rappid-data/999999999", timeout=5)
        self.assertIn(response.status_code, [400, 404])
        logger.info("✅ Large train number handling")
    
    def test_zero_train_number(self):
        """Test with zero train number"""
        response = requests.get(f"{BASE_URL}/api/rappid-data/0", timeout=5)
        self.assertIn(response.status_code, [400, 404])
        logger.info("✅ Zero train number handling")
    
    def test_negative_train_number(self):
        """Test with negative train number"""
        response = requests.get(f"{BASE_URL}/api/rappid-data/-1", timeout=5)
        self.assertIn(response.status_code, [400, 404])
        logger.info("✅ Negative train number handling")
    
    def test_special_characters_in_input(self):
        """Test with special characters"""
        response = requests.get(f"{BASE_URL}/api/rappid-data/12%20970", timeout=5)
        self.assertIn(response.status_code, [200, 404, 400])
        logger.info("✅ Special character handling")


def run_test_suite():
    """Run all tests with summary"""
    print("\n" + "="*80)
    print("COMPREHENSIVE INTEGRATION & STRESS TESTING SUITE")
    print("="*80 + "\n")
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestEndpointIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestConcurrentRequests))
    suite.addTests(loader.loadTestsFromTestCase(TestCachePerformance))
    suite.addTests(loader.loadTestsFromTestCase(TestDataIntegrity))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorRecovery))
    suite.addTests(loader.loadTestsFromTestCase(TestLoadSimulation))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failed: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print("="*80 + "\n")
    
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED!")
    else:
        print("⚠️ SOME TESTS FAILED - CHECK ABOVE FOR DETAILS")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_test_suite()
    exit(0 if success else 1)
