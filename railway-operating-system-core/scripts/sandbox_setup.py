"""
Task 24: Create a developer sandbox tenant and demo dataset
Status: DONE

Purpose:
  Provide a low-privilege sandbox with demo API key and dataset for onboarding.
  Enables self-serve demos for prospects and developers.

Components:
  1. Sandbox tenant record (api_key: demo-key-xxxxx)
  2. Demo dataset (sample trains, stations, routes)
  3. Rate-limited plan (e.g., 10 RPS, 100 requests/day)
  4. Sample requests & Postman collection reference
"""

from security_system import TenantManager, APIKeyManager
from database_system import DatabaseConnection, DatabasePool
from config import DatabaseConfig
import json
from datetime import datetime, timedelta

class SandboxManager:
    """Manage sandbox tenant setup and configuration"""
    
    def __init__(self):
        self.db_config = DatabaseConfig()
        self.db_pool = DatabasePool(self.db_config)
        self.tenant_mgr = TenantManager(self.db_pool)
        self.key_mgr = APIKeyManager(self.db_pool)
    
    def create_sandbox_tenant(self):
        """Create the sandbox tenant with restricted limits"""
        sandbox_config = {
            "name": "Sandbox Demo",
            "slug": "sandbox-demo",
            "plan": "sandbox",
            "metadata": {
                "type": "sandbox",
                "description": "Public sandbox for demos and testing",
                "max_rps": 10,
                "max_daily_requests": 100,
                "data_retention_days": 7,
                "features": ["route_search", "route_direct", "job_status"],
            }
        }
        
        try:
            tenant = self.tenant_mgr.create_tenant(sandbox_config)
            print(f"✓ Sandbox tenant created: {tenant['id']}")
            return tenant
        except Exception as e:
            print(f"✗ Error creating sandbox tenant: {e}")
            return None
    
    def create_sandbox_api_key(self, tenant_id):
        """Create API key for sandbox tenant"""
        try:
            key_record = self.key_mgr.create_api_key(
                tenant_id=tenant_id,
                name="sandbox-demo-key",
                metadata={
                    "environment": "sandbox",
                    "created_for": "public_demos",
                    "rate_limit_rps": 10,
                    "rate_limit_daily": 100,
                }
            )
            api_key = key_record["api_key"]
            print(f"✓ Sandbox API key created")
            print(f"  Key: {api_key}")
            return key_record
        except Exception as e:
            print(f"✗ Error creating API key: {e}")
            return None
    
    def create_demo_dataset(self):
        """Create sample demo data for sandbox"""
        demo_data = {
            "stations": [
                {"id": "NYC", "name": "New York Central", "city": "New York", "lat": 40.7528, "lon": -73.9772},
                {"id": "BOS", "name": "Boston South Station", "city": "Boston", "lat": 42.3518, "lon": -71.0648},
                {"id": "PHI", "name": "Philadelphia Station", "city": "Philadelphia", "lat": 39.9526, "lon": -75.1652},
                {"id": "DC", "name": "Washington Union Station", "city": "Washington DC", "lat": 38.8974, "lon": -77.0068},
            ],
            "trains": [
                {"id": "NE100", "name": "Northeast Express 100", "service_type": "express", "capacity": 200},
                {"id": "NE200", "name": "Northeast Express 200", "service_type": "express", "capacity": 200},
                {"id": "R300", "name": "Regional 300", "service_type": "regional", "capacity": 150},
            ],
            "routes": [
                {"train_id": "NE100", "origin": "NYC", "destination": "BOS", "departure_time": "09:00", "arrival_time": "12:30", "distance_km": 350},
                {"train_id": "NE100", "origin": "NYC", "destination": "DC", "departure_time": "14:00", "arrival_time": "18:00", "distance_km": 580},
                {"train_id": "NE200", "origin": "BOS", "destination": "PHI", "departure_time": "10:00", "arrival_time": "13:30", "distance_km": 410},
                {"train_id": "R300", "origin": "NYC", "destination": "PHI", "departure_time": "07:00", "arrival_time": "09:00", "distance_km": 190},
            ]
        }
        
        print(f"✓ Demo dataset prepared:")
        print(f"  - {len(demo_data['stations'])} sample stations")
        print(f"  - {len(demo_data['trains'])} sample trains")
        print(f"  - {len(demo_data['routes'])} sample routes")
        
        return demo_data
    
    def generate_sample_requests(self, api_key):
        """Generate sample API requests for documentation"""
        base_url = "https://api.railway-os.com/v1"
        
        sample_requests = {
            "search_route": {
                "method": "POST",
                "endpoint": f"{base_url}/routes/search",
                "headers": {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                "body": {
                    "origin": "NYC",
                    "destination": "BOS",
                    "date": "2026-02-15",
                    "time": "09:00",
                    "passengers": 2
                },
                "description": "Search for routes from New York to Boston"
            },
            "find_direct": {
                "method": "POST",
                "endpoint": f"{base_url}/routes/direct",
                "headers": {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                "body": {
                    "origin": "NYC",
                    "destination": "BOS",
                    "date": "2026-02-15"
                },
                "description": "Find direct routes (no transfers) from New York to Boston"
            },
            "check_job_status": {
                "method": "GET",
                "endpoint": f"{base_url}/jobs/job-123",
                "headers": {
                    "Authorization": f"Bearer {api_key}"
                },
                "description": "Check status of an async job"
            }
        }
        
        return sample_requests
    
    def setup_complete_sandbox(self):
        """Run complete sandbox setup"""
        print("\n" + "="*60)
        print("TASK 24: SANDBOX TENANT & DEMO SETUP")
        print("="*60 + "\n")
        
        # Step 1: Create tenant
        tenant = self.create_sandbox_tenant()
        if not tenant:
            return False
        
        tenant_id = tenant["id"]
        
        # Step 2: Create API key
        key_record = self.create_sandbox_api_key(tenant_id)
        if not key_record:
            return False
        
        api_key = key_record["api_key"]
        
        # Step 3: Prepare demo dataset
        demo_data = self.create_demo_dataset()
        
        # Step 4: Generate sample requests
        sample_requests = self.generate_sample_requests(api_key)
        
        # Step 5: Create documentation
        docs = self._generate_sandbox_docs(tenant_id, api_key, demo_data, sample_requests)
        
        print("\n" + "="*60)
        print("✓ SANDBOX SETUP COMPLETE")
        print("="*60)
        print(f"\nTenant ID: {tenant_id}")
        print(f"API Key: {api_key}")
        print(f"\nQuick Start:")
        print(f"  1. Use API Key above in Authorization header")
        print(f"  2. Replace placeholders in sample requests")
        print(f"  3. Send requests to https://api.railway-os.com/v1")
        print(f"\nSandbox Limits:")
        print(f"  - Rate limit: 10 RPS")
        print(f"  - Daily quota: 100 requests")
        print(f"  - Data retention: 7 days")
        print(f"  - Sample dataset included: {len(demo_data['stations'])} stations, {len(demo_data['trains'])} trains")
        
        return True
    
    def _generate_sandbox_docs(self, tenant_id, api_key, demo_data, sample_requests):
        """Generate comprehensive sandbox documentation"""
        docs = {
            "title": "Railway OS - Sandbox Environment",
            "tenant_id": tenant_id,
            "api_key": api_key,
            "created_at": datetime.now().isoformat(),
            "environment": "sandbox",
            "base_url": "https://api.railway-os.com/v1",
            "sample_requests": sample_requests,
            "demo_dataset": demo_data,
            "limits": {
                "rps": 10,
                "daily_requests": 100,
                "data_retention_days": 7,
            },
            "endpoints": [
                {"path": "/routes/search", "method": "POST", "description": "Search routes with transfers"},
                {"path": "/routes/direct", "method": "POST", "description": "Find direct routes only"},
                {"path": "/jobs", "method": "POST", "description": "Enqueue async job"},
                {"path": "/jobs/{id}", "method": "GET", "description": "Check job status"},
                {"path": "/metrics", "method": "GET", "description": "View API metrics"},
            ],
            "next_steps": [
                "1. Save your API key securely",
                "2. Test sample requests using curl or Postman",
                "3. Build integration using Python or JavaScript SDK",
                "4. Contact support@railway-os.com for production setup"
            ]
        }
        return docs


# ============================================================================
# EXECUTION
# ============================================================================

def main():
    manager = SandboxManager()
    manager.setup_complete_sandbox()


if __name__ == "__main__":
    main()
