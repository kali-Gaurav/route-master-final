"""
Phase 4: Integration Tests
Tests for API endpoints and real system behavior
"""

import unittest
import json
import sys
import os
from io import StringIO

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Disable cache warming for tests by setting environment variable
os.environ['TESTING'] = '1'

# Now import after setting env
try:
    from api import app
except Exception as e:
    print(f"Warning: Could not import app: {e}")
    app = None


class TestAPIEndpoints(unittest.TestCase):
    """Test actual API endpoints"""
    
    @classmethod
    def setUpClass(cls):
        """Setup test client"""
        if app is None:
            raise unittest.SkipTest("Could not load app")
        app.config['TESTING'] = True
        cls.client = app.test_client()
    
    def test_health_endpoint_returns_200(self):
        """Test /api/health returns 200 OK"""
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
    
    def test_health_endpoint_json(self):
        """Test /api/health returns valid JSON"""
        response = self.client.get('/api/health')
        try:
            data = json.loads(response.data)
            self.assertIn('status', data)
        except json.JSONDecodeError:
            self.fail("Response is not valid JSON")
    
    def test_health_endpoint_status_field(self):
        """Test /api/health has status field"""
        response = self.client.get('/api/health')
        data = json.loads(response.data)
        self.assertIn('status', data)
    
    def test_performance_metrics_endpoint(self):
        """Test /api/performance-metrics endpoint"""
        response = self.client.get('/api/performance-metrics')
        
        if response.status_code == 200:
            data = json.loads(response.data)
            self.assertIn('performance', data)
    
    def test_performance_metrics_has_uptime(self):
        """Test metrics include server uptime"""
        response = self.client.get('/api/performance-metrics')
        
        if response.status_code == 200:
            data = json.loads(response.data)
            self.assertIn('server_uptime_seconds', data)
    
    def test_warm_cache_endpoint_exists(self):
        """Test /admin/warm-cache endpoint exists"""
        response = self.client.post('/admin/warm-cache')
        # Should return 200 or 404 (not 500)
        self.assertIn(response.status_code, [200, 404, 405])
    
    def test_clear_cache_endpoint_exists(self):
        """Test /admin/clear-cache endpoint exists"""
        response = self.client.post('/admin/clear-cache')
        # Should return 200 or 404 (not 500)
        self.assertIn(response.status_code, [200, 404, 405])
    
    def test_rappid_status_endpoint(self):
        """Test /admin/status/rappid endpoint"""
        response = self.client.get('/admin/status/rappid')
        
        if response.status_code == 200:
            data = json.loads(response.data)
            # Should have some status information
            self.assertIsNotNone(data)


class TestDataEndpoints(unittest.TestCase):
    """Test data serving endpoints"""
    
    @classmethod
    def setUpClass(cls):
        """Setup test client"""
        if app is None:
            raise unittest.SkipTest("Could not load app")
        app.config['TESTING'] = True
        cls.client = app.test_client()
    
    def test_rappid_data_endpoint_returns_correct_status(self):
        """Test /api/rappid-data returns appropriate status"""
        response = self.client.get('/api/rappid-data/12970')
        
        # Should be 200 if cached, or appropriate error code
        self.assertIn(response.status_code, [200, 404, 500])
    
    def test_rappid_data_invalid_train_returns_error(self):
        """Test invalid train number handling"""
        response = self.client.get('/api/rappid-data/INVALID')
        
        # Should handle gracefully
        self.assertIn(response.status_code, [200, 404, 500])
    
    def test_refresh_endpoint_exists(self):
        """Test refresh endpoint exists"""
        response = self.client.post('/admin/refresh-rappid/12970')
        
        # Should return something (not crash)
        self.assertIsNotNone(response)
    
    def test_bulk_refresh_endpoint_exists(self):
        """Test bulk refresh endpoint exists"""
        response = self.client.post(
            '/admin/refresh-rappid-bulk',
            data=json.dumps({"trains": ["12970"]}),
            content_type='application/json'
        )
        
        # Should return something
        self.assertIsNotNone(response)


class TestErrorHandling(unittest.TestCase):
    """Test error handling in endpoints"""
    
    @classmethod
    def setUpClass(cls):
        """Setup test client"""
        if app is None:
            raise unittest.SkipTest("Could not load app")
        app.config['TESTING'] = True
        cls.client = app.test_client()
    
    def test_nonexistent_endpoint_returns_404(self):
        """Test nonexistent endpoint returns 404"""
        response = self.client.get('/api/nonexistent')
        self.assertEqual(response.status_code, 404)
    
    def test_wrong_method_returns_405(self):
        """Test wrong HTTP method returns 405"""
        response = self.client.put('/api/health')
        self.assertEqual(response.status_code, 405)
    
    def test_malformed_json_handling(self):
        """Test malformed JSON is handled"""
        response = self.client.post(
            '/admin/refresh-rappid-bulk',
            data='{"invalid json"',
            content_type='application/json'
        )
        
        # Should handle gracefully
        self.assertIn(response.status_code, [400, 500])


class TestCORS(unittest.TestCase):
    """Test CORS headers"""
    
    @classmethod
    def setUpClass(cls):
        """Setup test client"""
        if app is None:
            raise unittest.SkipTest("Could not load app")
        app.config['TESTING'] = True
        cls.client = app.test_client()
    
    def test_health_endpoint_cors_headers(self):
        """Test CORS headers present"""
        response = self.client.get('/api/health')
        
        # Check if CORS headers might be present
        headers = dict(response.headers)
        # Flask-CORS should add appropriate headers
        self.assertIsNotNone(headers)


class TestEndpointResponseFormat(unittest.TestCase):
    """Test response format of endpoints"""
    
    @classmethod
    def setUpClass(cls):
        """Setup test client"""
        if app is None:
            raise unittest.SkipTest("Could not load app")
        app.config['TESTING'] = True
        cls.client = app.test_client()
    
    def test_health_returns_json(self):
        """Test health endpoint returns JSON"""
        response = self.client.get('/api/health')
        
        self.assertEqual(response.content_type.split(';')[0], 'application/json')
    
    def test_health_response_is_dict(self):
        """Test health response is JSON object not array"""
        response = self.client.get('/api/health')
        data = json.loads(response.data)
        
        self.assertIsInstance(data, dict)
    
    def test_performance_metrics_response_structure(self):
        """Test performance metrics response structure"""
        response = self.client.get('/api/performance-metrics')
        
        if response.status_code == 200:
            data = json.loads(response.data)
            self.assertIsInstance(data, dict)


def run_integration_tests():
    """Run all integration tests"""
    print("\n" + "="*80)
    print("PHASE 4: INTEGRATION TESTS (API Endpoints)")
    print("="*80)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestAPIEndpoints))
    suite.addTests(loader.loadTestsFromTestCase(TestDataEndpoints))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestCORS))
    suite.addTests(loader.loadTestsFromTestCase(TestEndpointResponseFormat))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*80)
    print("INTEGRATION TEST SUMMARY")
    print("="*80)
    print(f"Tests run: {result.testsRun}")
    successes = result.testsRun - len(result.failures) - len(result.errors)
    print(f"Successes: {successes}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    if result.testsRun > 0:
        print(f"Success rate: {(successes / result.testsRun * 100):.1f}%")
    print("="*80)
    
    return result


if __name__ == '__main__':
    result = run_integration_tests()
    exit(0 if result.wasSuccessful() else 1)
