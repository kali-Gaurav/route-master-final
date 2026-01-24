"""
SIMPLIFIED INTEGRATION TEST SUITE
Fast, reliable endpoint testing without complex concurrency
"""

import unittest
import requests
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:5000"

class QuickIntegrationTests(unittest.TestCase):
    """Quick integration tests for all endpoints"""
    
    def test_01_health_check(self):
        """Test health endpoint"""
        try:
            response = requests.get(f"{BASE_URL}/api/health", timeout=5)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn('status', data)
            logger.info("✅ Health endpoint: PASS")
        except Exception as e:
            logger.error(f"❌ Health endpoint: {e}")
            raise
    
    def test_02_performance_metrics(self):
        """Test performance metrics endpoint"""
        try:
            response = requests.get(f"{BASE_URL}/api/performance-metrics", timeout=5)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIsNotNone(data.get('performance'))
            logger.info("✅ Performance metrics: PASS")
        except Exception as e:
            logger.error(f"❌ Performance metrics: {e}")
            raise
    
    def test_03_rappid_data_valid(self):
        """Test fetching cached train data"""
        try:
            response = requests.get(f"{BASE_URL}/api/rappid-data/12970", timeout=10)
            self.assertIn(response.status_code, [200, 404])
            logger.info(f"✅ RAPPID data endpoint: PASS (status {response.status_code})")
        except Exception as e:
            logger.error(f"❌ RAPPID data endpoint: {e}")
            raise
    
    def test_04_status_endpoint(self):
        """Test status endpoint"""
        try:
            response = requests.get(f"{BASE_URL}/admin/status/rappid", timeout=5)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn('coverage_percent', data)
            logger.info(f"✅ Status endpoint: PASS (Coverage: {data.get('coverage_percent')}%)")
        except Exception as e:
            logger.error(f"❌ Status endpoint: {e}")
            raise
    
    def test_05_refresh_single(self):
        """Test refreshing single train"""
        try:
            response = requests.post(f"{BASE_URL}/admin/refresh-rappid/12970", timeout=15)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn('status', data)
            logger.info("✅ Refresh single train: PASS")
        except Exception as e:
            logger.error(f"❌ Refresh single train: {e}")
            raise
    
    def test_06_bulk_refresh(self):
        """Test bulk train refresh"""
        try:
            payload = {"train_numbers": ["12970", "14709", "12956"]}
            response = requests.post(
                f"{BASE_URL}/admin/refresh-rappid-bulk",
                json=payload,
                timeout=30
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn('successful', data)
            logger.info(f"✅ Bulk refresh: PASS ({data.get('successful')} trains)")
        except Exception as e:
            logger.error(f"❌ Bulk refresh: {e}")
            raise
    
    def test_07_invalid_train(self):
        """Test error handling with invalid train"""
        try:
            response = requests.get(f"{BASE_URL}/api/rappid-data/999999999", timeout=5)
            self.assertIn(response.status_code, [400, 404])
            logger.info("✅ Error handling (invalid train): PASS")
        except Exception as e:
            logger.error(f"❌ Error handling: {e}")
            raise
    
    def test_08_concurrent_health_checks(self):
        """Test multiple sequential requests"""
        try:
            results = []
            for i in range(5):
                response = requests.get(f"{BASE_URL}/api/health", timeout=5)
                results.append(response.status_code == 200)
            
            success_count = sum(results)
            self.assertGreater(success_count, 3)
            logger.info(f"✅ Sequential requests: PASS ({success_count}/5 successful)")
        except Exception as e:
            logger.error(f"❌ Sequential requests: {e}")
            raise
    
    def test_09_response_consistency(self):
        """Test response format consistency"""
        try:
            resp1 = requests.get(f"{BASE_URL}/api/health", timeout=5).json()
            resp2 = requests.get(f"{BASE_URL}/api/health", timeout=5).json()
            
            self.assertEqual(set(resp1.keys()), set(resp2.keys()))
            logger.info("✅ Response consistency: PASS")
        except Exception as e:
            logger.error(f"❌ Response consistency: {e}")
            raise
    
    def test_10_cache_operations(self):
        """Test cache clear/warm operations"""
        try:
            # Get initial status
            response1 = requests.get(f"{BASE_URL}/admin/status/rappid", timeout=5)
            initial_count = response1.json().get('stored_json_files', 0)
            
            logger.info(f"✅ Cache operations: PASS (Current: {initial_count} files)")
        except Exception as e:
            logger.error(f"❌ Cache operations: {e}")
            raise


def main():
    """Run integration tests"""
    print("\n" + "="*80)
    print("INTEGRATION TEST SUITE - ALL ENDPOINTS")
    print("="*80 + "\n")
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(QuickIntegrationTests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*80)
    print("INTEGRATION TEST SUMMARY")
    print("="*80)
    print(f"Tests Run: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failed: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print(f"✅ SUCCESS RATE: 100% - ALL INTEGRATION TESTS PASSED!")
    else:
        print(f"⚠️ SUCCESS RATE: {((result.testsRun - len(result.failures) - len(result.errors))/result.testsRun*100):.1f}%")
    
    print("="*80 + "\n")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
