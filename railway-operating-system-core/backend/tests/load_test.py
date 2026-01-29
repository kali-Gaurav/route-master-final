# tests/load_test.py
"""Load testing suite using Locust"""

from locust import HttpUser, task, between  # type: ignore
import json
import random
import string

class RailwayAPIUser(HttpUser):
    """Load testing user for Railway Operating System API"""

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    def on_start(self):
        """Setup before starting tasks"""
        # Register a test user
        self.username = f"loadtest_{random.randint(1000, 9999)}"
        self.email = f"{self.username}@test.com"
        self.password = "TestPass123!"

        # Try to register (may fail if user exists, that's ok)
        try:
            response = self.client.post("/v1/auth/register", json={
                "username": self.username,
                "email": self.email,
                "password": self.password,
                "first_name": "Load",
                "last_name": "Test",
                "role": "user"
            })
            if response.status_code == 200:
                # Login to get token
                login_response = self.client.post("/v1/auth/login", data={
                    "username": self.email,
                    "password": self.password
                })
                if login_response.status_code == 200:
                    self.token = login_response.json().get("access_token")
                    self.headers = {"Authorization": f"Bearer {self.token}"}
                else:
                    self.headers = {}
            else:
                self.headers = {}
        except:
            self.headers = {}

    @task(1)
    def health_check(self):
        """Test health endpoint"""
        self.client.get("/health")

    @task(1)
    def readiness_check(self):
        """Test readiness endpoint"""
        self.client.get("/ready")

    @task(2)
    def get_routes(self):
        """Test route listing with pagination"""
        params = {
            "skip": random.randint(0, 100),
            "limit": random.randint(10, 50)
        }
        self.client.get("/v1/routes", params=params, headers=self.headers)

    @task(1)
    def search_routes(self):
        """Test route search"""
        search_terms = ["station", "route", "train", "express"]
        params = {
            "search": random.choice(search_terms),
            "limit": random.randint(5, 20)
        }
        self.client.get("/v1/routes/search", params=params, headers=self.headers)

    @task(1)
    def get_user_profile(self):
        """Test user profile access"""
        if hasattr(self, 'headers') and self.headers:
            self.client.get("/v1/auth/me", headers=self.headers)

    @task(1)
    def create_job(self):
        """Test job creation"""
        if hasattr(self, 'headers') and self.headers:
            job_data = {
                "title": f"Load Test Job {random.randint(1, 1000)}",
                "description": "Load testing job creation",
                "type": "route_analysis",
                "payload": {"test": True}
            }
            self.client.post("/v1/jobs", json=job_data, headers=self.headers)

    @task(1)
    def get_jobs(self):
        """Test job listing"""
        if hasattr(self, 'headers') and self.headers:
            params = {
                "skip": random.randint(0, 50),
                "limit": random.randint(5, 20)
            }
            self.client.get("/v1/jobs", params=params, headers=self.headers)

    @task(1)
    def api_docs_access(self):
        """Test API documentation access"""
        self.client.get("/docs")

    @task(1)
    def openapi_json(self):
        """Test OpenAPI JSON access"""
        self.client.get("/openapi.json")

# Configuration for different load scenarios
class LightLoadUser(RailwayAPIUser):
    """Light load scenario: 1-2 users per second"""
    wait_time = between(0.5, 1.5)

class MediumLoadUser(RailwayAPIUser):
    """Medium load scenario: 5-10 users per second"""
    wait_time = between(0.1, 0.5)

class HeavyLoadUser(RailwayAPIUser):
    """Heavy load scenario: 20+ users per second"""
    wait_time = between(0.05, 0.2)

# To run the load test:
# locust -f backend/tests/load_test.py --host=http://localhost:8000
#
# Or specify user class:
# locust -f backend/tests/load_test.py --host=http://localhost:8000 RailwayAPIUser
#
# For web interface:
# locust -f backend/tests/load_test.py --host=http://localhost:8000 --web-host=127.0.0.1 --web-port=8089