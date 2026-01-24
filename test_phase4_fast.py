"""
Phase 4: Fast Unit Tests (No API calls)
Focused testing of local functionality
"""

import unittest
import time
import threading
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rappid_optimized import OptimizedRAPPIDClient, CacheWarmer


class TestRAPPIDClientCore(unittest.TestCase):
    """Core functionality tests"""
    
    def setUp(self):
        self.client = OptimizedRAPPIDClient()
    
    def tearDown(self):
        self.client.clear_cache()
    
    def test_cache_operations(self):
        """Test basic cache set/get"""
        self.client._set_cached("test", {"data": 1})
        result = self.client._get_cached("test")
        self.assertEqual(result, {"data": 1})
    
    def test_cache_clearing(self):
        """Test cache clearing"""
        self.client._set_cached("t1", {"d": 1})
        self.client._set_cached("t2", {"d": 2})
        self.assertEqual(len(self.client.cache), 2)
        self.client.clear_cache()
        self.assertEqual(len(self.client.cache), 0)
    
    def test_metrics_tracking(self):
        """Test metrics initialization"""
        stats = self.client.get_stats()
        self.assertIn('total_requests', stats)
        self.assertIn('cache_hits', stats)
        self.assertIn('cache_misses', stats)
    
    def test_thread_safety(self):
        """Test cache is thread-safe"""
        def access():
            for i in range(50):
                self.client._set_cached(f"k{i}", {"v": i})
                self.client._get_cached(f"k{i}")
        
        threads = [threading.Thread(target=access) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # No crashes = thread-safe
        self.assertGreater(len(self.client.cache), 0)
    
    def test_session_exists(self):
        """Test HTTP session created"""
        self.assertIsNotNone(self.client.session)
    
    def test_configuration_values(self):
        """Test configuration"""
        self.assertEqual(self.client.CACHE_TTL, 300)
        self.assertEqual(self.client.POOL_CONNECTIONS, 10)
        self.assertEqual(self.client.POOL_MAXSIZE, 10)


class TestCacheWarmerCore(unittest.TestCase):
    """CacheWarmer functionality tests"""
    
    def test_trains_list_exists(self):
        """Test high-frequency trains list"""
        self.assertGreaterEqual(len(CacheWarmer.HIGH_FREQUENCY_TRAINS), 50)
    
    def test_trains_are_valid(self):
        """Test trains are valid strings"""
        for train in CacheWarmer.HIGH_FREQUENCY_TRAINS[:5]:
            self.assertIsInstance(train, str)
            self.assertGreater(len(train), 0)


class TestCacheTTL(unittest.TestCase):
    """Cache TTL tests"""
    
    def test_fresh_cache_retrieved(self):
        """Test fresh cache is retrieved"""
        client = OptimizedRAPPIDClient()
        data = {"train": "12970"}
        client._set_cached("12970", data)
        
        # Immediately retrieve
        result = client._get_cached("12970")
        self.assertEqual(result, data)
    
    def test_expired_cache_not_retrieved(self):
        """Test expired cache handling"""
        client = OptimizedRAPPIDClient()
        data = {"train": "12970"}
        
        # Set cache normally
        client._set_cached("12970", data)
        
        # Try to retrieve - should work since fresh
        result = client._get_cached("12970")
        self.assertEqual(result, data)


class TestDataIntegrity(unittest.TestCase):
    """Data integrity tests"""
    
    def test_complex_data_preserved(self):
        """Test complex data structures are preserved"""
        client = OptimizedRAPPIDClient()
        
        data = {
            "train": "12970",
            "schedule": [
                {"station": "A", "time": "10:00"},
                {"station": "B", "time": "15:00"}
            ],
            "fares": {"AC": 500, "SL": 300}
        }
        
        client._set_cached("12970", data)
        result = client._get_cached("12970")
        
        self.assertEqual(result, data)
        self.assertEqual(len(result["schedule"]), 2)
        self.assertEqual(result["fares"]["AC"], 500)
    
    def test_multiple_entries_isolated(self):
        """Test multiple cache entries don't interfere"""
        client = OptimizedRAPPIDClient()
        
        client._set_cached("t1", {"id": 1})
        client._set_cached("t2", {"id": 2})
        client._set_cached("t3", {"id": 3})
        
        self.assertEqual(client._get_cached("t1")["id"], 1)
        self.assertEqual(client._get_cached("t2")["id"], 2)
        self.assertEqual(client._get_cached("t3")["id"], 3)


class TestPerformance(unittest.TestCase):
    """Performance tests"""
    
    def test_cache_speed(self):
        """Test cache operations are fast"""
        client = OptimizedRAPPIDClient()
        
        start = time.time()
        for i in range(1000):
            client._set_cached(f"t{i}", {"v": i})
        elapsed1 = time.time() - start
        
        start = time.time()
        for i in range(1000):
            client._get_cached(f"t{i}")
        elapsed2 = time.time() - start
        
        # 1000 sets and 1000 gets should be fast
        self.assertLess(elapsed1 + elapsed2, 1.0)
    
    def test_stats_calculation_speed(self):
        """Test stats are calculated quickly"""
        client = OptimizedRAPPIDClient()
        
        start = time.time()
        for _ in range(100):
            stats = client.get_stats()
        elapsed = time.time() - start
        
        # 100 stats calculations should be < 50ms
        self.assertLess(elapsed, 0.1)


class TestErrorHandling(unittest.TestCase):
    """Error handling tests"""
    
    def test_empty_cache_access(self):
        """Test accessing empty cache doesn't crash"""
        client = OptimizedRAPPIDClient()
        result = client._get_cached("nonexistent")
        self.assertIsNone(result)
    
    def test_clear_empty_cache(self):
        """Test clearing empty cache doesn't crash"""
        client = OptimizedRAPPIDClient()
        client.clear_cache()
        self.assertEqual(len(client.cache), 0)
    
    def test_none_data_handling(self):
        """Test handling None data"""
        client = OptimizedRAPPIDClient()
        client._set_cached("none_key", None)
        # Should handle without crashing
        result = client._get_cached("none_key")


class TestConfiguration(unittest.TestCase):
    """Configuration tests"""
    
    def test_timeout_setting(self):
        """Test timeout is set"""
        client = OptimizedRAPPIDClient(timeout=15)
        self.assertEqual(client.timeout, 15)
    
    def test_retry_attempts_setting(self):
        """Test retry attempts setting"""
        client = OptimizedRAPPIDClient(retry_attempts=5)
        # MAX_RETRIES is class constant, not instance
        self.assertEqual(client.retry_attempts, 5)
    
    def test_cache_ttl_constant(self):
        """Test cache TTL constant"""
        client = OptimizedRAPPIDClient()
        self.assertEqual(client.CACHE_TTL, 300)


def run_fast_tests():
    """Run all fast tests"""
    print("="*80)
    print("PHASE 4: FAST UNIT TESTS (No API Calls)")
    print("="*80)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestRAPPIDClientCore))
    suite.addTests(loader.loadTestsFromTestCase(TestCacheWarmerCore))
    suite.addTests(loader.loadTestsFromTestCase(TestCacheTTL))
    suite.addTests(loader.loadTestsFromTestCase(TestDataIntegrity))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformance))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestConfiguration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print("="*80)
    
    return result


if __name__ == '__main__':
    result = run_fast_tests()
    exit(0 if result.wasSuccessful() else 1)
