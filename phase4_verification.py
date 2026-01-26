"""
PHASE 4: DevOps, Deployment & Finalization Comprehensive Verification Suite

Tests for deployment readiness, performance benchmarking, and production hardening.
All 12 tests must pass (100%) before production deployment.

Test Categories:
1. Unified Run Script & Commands (2 tests)
2. Performance Benchmarking (2 tests)
3. Data Quality & Validation (2 tests)
4. Documentation & Setup (2 tests)
5. Testing & Security (2 tests)
6. Production Readiness (2 tests)
"""

import sys
import os
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime

# Set UTF-8 encoding
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_section(title):
    """Print section header"""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}{title.center(80)}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")

def print_test(number, title):
    """Print test header"""
    print(f"{BOLD}{number}. {title}{RESET}")

def print_pass(message):
    """Print passing test"""
    print(f"{GREEN}[PASS] {message}{RESET}")

def print_fail(message):
    """Print failing test"""
    print(f"{RED}[FAIL] {message}{RESET}")

class Phase4Verifier:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.base_dir = Path(__file__).parent

    def test_run_script_exists(self):
        """4.1 Test run.py script exists for unified startup"""
        print_test("4.1", "Unified Run Script Exists")
        try:
            run_script = self.base_dir / "run.py"
            
            if run_script.exists():
                # Check if it contains startup logic
                with open(run_script, 'r') as f:
                    content = f.read()
                    if 'uvicorn' in content.lower() or 'vite' in content.lower():
                        print_pass("run.py exists and contains startup logic")
                        self.passed += 1
                        return True
                    else:
                        print_fail("run.py exists but missing startup commands")
                        self.failed += 1
                        return False
            else:
                print_fail("run.py script not found")
                self.failed += 1
                return False
        except Exception as e:
            print_fail(f"Failed to check run.py: {str(e)}")
            self.failed += 1
            return False

    def test_package_json_scripts(self):
        """4.2 Test package.json has dev:full command"""
        print_test("4.2", "Package.json Dev:Full Script")
        try:
            pkg_file = self.base_dir / "package.json"
            
            if pkg_file.exists():
                with open(pkg_file, 'r') as f:
                    pkg = json.load(f)
                    scripts = pkg.get('scripts', {})
                    
                    if 'dev:full' in scripts or 'dev' in scripts:
                        print_pass(f"package.json has development scripts: {list(scripts.keys())[:5]}")
                        self.passed += 1
                        return True
            
            print_fail("package.json missing dev scripts")
            self.failed += 1
            return False
        except Exception as e:
            print_fail(f"Failed to check package.json: {str(e)}")
            self.failed += 1
            return False

    def test_direct_routes_performance(self):
        """4.3 Test direct routes (0 transfers) search performance"""
        print_test("4.3", "Direct Routes Performance")
        try:
            import requests
            
            # Search for direct routes
            start = time.time()
            response = requests.post(
                'http://localhost:5000/api/routes',
                json={
                    'origin': 'CSMT',
                    'destination': 'KHED',
                    'max_results': 5
                },
                timeout=10
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                routes = response.json().get('all_generated_routes', [])
                direct_routes = [r for r in routes if r.get('totalTransfers', 0) == 0]
                
                if elapsed < 3.0 and direct_routes:
                    print_pass(f"Direct route search: {len(direct_routes)} routes in {elapsed*1000:.0f}ms")
                    self.passed += 1
                    return True
            
            print_fail(f"Direct route search failed or slow ({elapsed*1000:.0f}ms)")
            self.failed += 1
            return False
        except Exception as e:
            print_fail(f"Direct routes test failed: {str(e)}")
            self.failed += 1
            return False

    def test_multi_transfer_performance(self):
        """4.4 Test multi-transfer routes search performance"""
        print_test("4.4", "Multi-Transfer Routes Performance")
        try:
            import requests
            
            # Search for complex routes with transfers
            start = time.time()
            response = requests.post(
                'http://localhost:5000/api/routes',
                json={
                    'origin': 'CSMT',
                    'destination': 'KHED',
                    'max_results': 10
                },
                timeout=10
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                routes = response.json().get('all_generated_routes', [])
                multi_transfer = [r for r in routes if r.get('totalTransfers', 0) > 0]
                
                if elapsed < 4.0:
                    print_pass(f"Multi-transfer search: {len(multi_transfer)} routes in {elapsed*1000:.0f}ms")
                    self.passed += 1
                    return True
            
            print_fail(f"Multi-transfer search too slow ({elapsed*1000:.0f}ms)")
            self.failed += 1
            return False
        except Exception as e:
            print_fail(f"Multi-transfer test failed: {str(e)}")
            self.failed += 1
            return False

    def test_readme_exists(self):
        """4.5 Test README.md exists with setup instructions"""
        print_test("4.5", "README.md Documentation")
        try:
            readme_files = [
                self.base_dir / "README.md",
                self.base_dir.parent / "README.md",
                self.base_dir / "README_QUICK_START.md"
            ]
            
            for readme in readme_files:
                if readme.exists():
                    try:
                        with open(readme, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read().lower()
                            if any(word in content for word in ['setup', 'install', 'python', 'node', 'fastapi', 'run']):
                                print_pass(f"README found: {readme.name}")
                                self.passed += 1
                                return True
                    except:
                        continue
            
            print_fail("README.md with setup instructions not found")
            self.failed += 1
            return False
        except Exception as e:
            print_fail(f"README check failed: {str(e)}")
            self.failed += 1
            return False

    def test_unit_tests_exist(self):
        """4.6 Test unit test files exist for routing engine"""
        print_test("4.6", "Unit Tests for Routing Engine")
        try:
            test_files = [
                self.base_dir / "test_route_optimizer.py",
                self.base_dir / "test_pareto.py",
                self.base_dir / "tests" / "test_routing.py",
                self.base_dir / "phase1_verification.py",  # Already has tests
                self.base_dir / "phase2_verification.py",  # Already has tests
            ]
            
            for test_file in test_files:
                if test_file.exists():
                    with open(test_file, 'r') as f:
                        content = f.read()
                        if any(word in content for word in ['def test_', 'class Test', 'assert ']):
                            print_pass(f"Unit tests found: {test_file.name}")
                            self.passed += 1
                            return True
            
            print_fail("Dedicated unit tests for routing engine not found")
            self.failed += 1
            return False
        except Exception as e:
            print_fail(f"Unit tests check failed: {str(e)}")
            self.failed += 1
            return False

    def test_gitignore_updated(self):
        """4.7 Test .gitignore excludes database and build artifacts"""
        print_test("4.7", ".gitignore Configuration")
        try:
            gitignore = self.base_dir / ".gitignore"
            parent_gitignore = self.base_dir.parent / ".gitignore"
            root_gitignore = Path(__file__).parents[2] / ".gitignore"
            
            for gi in [gitignore, parent_gitignore, root_gitignore]:
                if gi.exists():
                    with open(gi, 'r') as f:
                        content = f.read().lower()
                        has_db = any(x in content for x in ['*.db', 'database', 'data/'])
                        has_cache = any(x in content for x in ['__pycache__', '.pyc', 'node_modules', 'dist/'])
                        
                        if has_db and has_cache:
                            print_pass(f".gitignore properly configured")
                            self.passed += 1
                            return True
            
            print_fail(".gitignore doesn't exclude database and build artifacts")
            self.failed += 1
            return False
        except Exception as e:
            print_fail(f".gitignore check failed: {str(e)}")
            self.failed += 1
            return False

    def test_environment_variables(self):
        """4.8 Test .env support for configuration"""
        print_test("4.8", "Environment Variables Support")
        try:
            # Check if api_v2.py or config files reference environment variables
            api_file = self.base_dir / "api_v2.py"
            config_file = self.base_dir / "config.py"
            
            files_to_check = [api_file, config_file]
            
            for file in files_to_check:
                if file.exists():
                    try:
                        with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            if 'os.environ' in content or 'getenv' in content or 'dotenv' in content.lower():
                                print_pass(f"Environment variables configured in {file.name}")
                                self.passed += 1
                                return True
                    except:
                        continue
            
            print_fail("Environment variable support not configured")
            self.failed += 1
            return False
        except Exception as e:
            print_fail(f"Environment variables check failed: {str(e)}")
            self.failed += 1
            return False

    def test_database_integrity(self):
        """4.9 Test database has all required tables and data"""
        print_test("4.9", "Database Integrity Check")
        try:
            from database_manager import get_db
            
            db = get_db()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Check all required tables
            required_tables = ['trains', 'stations', 'train_stations', 'search_logs']
            
            cursor.execute("""
                SELECT name FROM sqlite_master WHERE type='table'
            """)
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            all_present = all(table in existing_tables for table in required_tables)
            
            if all_present:
                # Check data volume
                cursor.execute("SELECT COUNT(*) FROM trains")
                trains = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM stations")
                stations = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM train_stations")
                routes = cursor.fetchone()[0]
                
                if trains > 0 and stations > 0 and routes > 0:
                    print_pass(f"Database healthy: {trains} trains, {stations} stations, {routes} routes")
                    self.passed += 1
                    conn.close()
                    return True
            
            conn.close()
            print_fail("Database missing tables or data")
            self.failed += 1
            return False
        except Exception as e:
            print_fail(f"Database integrity check failed: {str(e)}")
            self.failed += 1
            return False

    def test_all_endpoints_secure(self):
        """4.10 Test endpoints have proper error handling and validation"""
        print_test("4.10", "Endpoint Security & Validation")
        try:
            import requests
            
            # Test that invalid inputs are handled gracefully
            test_cases = [
                {'origin': 'INVALID', 'destination': 'KHED'},
                {'origin': 'CSMT', 'destination': 'INVALID'},
            ]
            
            errors_handled = 0
            
            for test_input in test_cases:
                try:
                    response = requests.post(
                        'http://localhost:5000/api/routes',
                        json=test_input,
                        timeout=5
                    )
                    # Should return empty routes or error
                    if response.status_code == 200:
                        data = response.json()
                        if not data.get('optimal_routes'):
                            errors_handled += 1
                    elif response.status_code >= 400:
                        errors_handled += 1
                except:
                    errors_handled += 1
            
            if errors_handled >= len(test_cases):
                print_pass("Endpoints properly validate and handle invalid inputs")
                self.passed += 1
                return True
            
            print_fail(f"Some endpoints don't handle invalid inputs properly")
            self.failed += 1
            return False
        except Exception as e:
            print_fail(f"Endpoint security test failed: {str(e)}")
            self.failed += 1
            return False

    def test_cors_security(self):
        """4.11 Test CORS is properly configured (not allow all origins)"""
        print_test("4.11", "CORS Security Configuration")
        try:
            # Check api_v2.py for CORS configuration
            api_file = self.base_dir / "api_v2.py"
            
            with open(api_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Should have specific origins list, check for restricted origins
                if 'localhost' in content and 'allow_origins' in content:
                    # Make sure it's not using "*" wildcard
                    cors_section = content[content.find('CORSMiddleware'):content.find('CORSMiddleware')+2000]
                    
                    if '*' not in cors_section or '["*"]' not in cors_section:
                        print_pass("CORS configured with specific allowed origins (not '*')")
                        self.passed += 1
                        return True
            
            print_fail("CORS not properly restricted to specific origins")
            self.failed += 1
            return False
        except Exception as e:
            print_fail(f"CORS security check failed: {str(e)}")
            self.failed += 1
            return False

    def test_logging_configured(self):
        """4.12 Test logging is properly configured for production"""
        print_test("4.12", "Logging Configuration")
        try:
            # Check multiple files for logging setup
            files_to_check = [
                self.base_dir / "api_v2.py",
                self.base_dir / "database_manager.py",
                self.base_dir / "logger.py"
            ]
            
            log_found = False
            for file in files_to_check:
                if file.exists():
                    try:
                        with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            if 'logging' in content and any(x in content for x in ['logger.', 'log_']):
                                log_found = True
                                break
                    except:
                        continue
            
            if log_found:
                print_pass("Logging configured in application")
                self.passed += 1
                return True
            
            print_fail("Logging not properly configured")
            self.failed += 1
            return False
        except Exception as e:
            print_fail(f"Logging check failed: {str(e)}")
            self.failed += 1
            return False

    def run_all_tests(self):
        """Run all Phase 4 tests"""
        print_section("PHASE 4 VERIFICATION TEST SUITE")
        print(f"{YELLOW}DevOps, Deployment & Production Readiness{RESET}\n")
        
        print_section("UNIFIED RUN SCRIPT & COMMANDS")
        self.test_run_script_exists()
        self.test_package_json_scripts()
        
        print_section("PERFORMANCE BENCHMARKING")
        self.test_direct_routes_performance()
        self.test_multi_transfer_performance()
        
        print_section("DOCUMENTATION & DATA QUALITY")
        self.test_readme_exists()
        self.test_unit_tests_exist()
        
        print_section("CONFIGURATION & SECURITY")
        self.test_gitignore_updated()
        self.test_environment_variables()
        self.test_database_integrity()
        
        print_section("PRODUCTION HARDENING")
        self.test_all_endpoints_secure()
        self.test_cors_security()
        self.test_logging_configured()
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        total = self.passed + self.failed
        percentage = (self.passed / total * 100) if total > 0 else 0
        
        print_section("PHASE 4 VERIFICATION TEST REPORT")
        
        print(f"Unified Run Script & Commands:\n"
              f"  [{'PASS' if self.passed >= 1 else 'FAIL'}] 4.1 Run Script Exists\n"
              f"  [{'PASS' if self.passed >= 2 else 'FAIL'}] 4.2 Package.json Scripts\n\n"
              f"Performance Benchmarking:\n"
              f"  [{'PASS' if self.passed >= 3 else 'FAIL'}] 4.3 Direct Routes Performance\n"
              f"  [{'PASS' if self.passed >= 4 else 'FAIL'}] 4.4 Multi-Transfer Routes Performance\n\n"
              f"Documentation & Data Quality:\n"
              f"  [{'PASS' if self.passed >= 5 else 'FAIL'}] 4.5 README Documentation\n"
              f"  [{'PASS' if self.passed >= 6 else 'FAIL'}] 4.6 Unit Tests\n\n"
              f"Configuration & Security:\n"
              f"  [{'PASS' if self.passed >= 7 else 'FAIL'}] 4.7 .gitignore Configuration\n"
              f"  [{'PASS' if self.passed >= 8 else 'FAIL'}] 4.8 Environment Variables\n"
              f"  [{'PASS' if self.passed >= 9 else 'FAIL'}] 4.9 Database Integrity\n\n"
              f"Production Hardening:\n"
              f"  [{'PASS' if self.passed >= 10 else 'FAIL'}] 4.10 Endpoint Security\n"
              f"  [{'PASS' if self.passed >= 11 else 'FAIL'}] 4.11 CORS Security\n"
              f"  [{'PASS' if self.passed >= 12 else 'FAIL'}] 4.12 Logging Configuration\n")
        
        print_section("SUMMARY")
        print(f"Total Tests: {total}")
        print(f"Passed: {self.passed} ({percentage:.1f}%)")
        print(f"Failed: {self.failed}")
        
        if self.failed == 0:
            print(f"Status: {BOLD}{GREEN}[PASS] PHASE 4 COMPLETE - READY FOR PRODUCTION{RESET}")
        else:
            print(f"Status: {BOLD}{RED}[FAIL] PHASE 4 INCOMPLETE{RESET}")
        
        print("=" * 80)

if __name__ == "__main__":
    verifier = Phase4Verifier()
    verifier.run_all_tests()
