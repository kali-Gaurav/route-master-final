"""
VERCEL DEPLOYMENT VALIDATION SCRIPT
Validates that all necessary configurations are in place for Vercel deployment

Run before deploying to Vercel to ensure everything is configured correctly.
"""

import os
import json
import sys
from pathlib import Path
from typing import List, Tuple

class VercelDeploymentValidator:
    """Validates Vercel deployment readiness"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.checks_passed = []
        self.checks_failed = []
        self.warnings = []
    
    def check_file_exists(self, filename: str, description: str) -> bool:
        """Check if a file exists"""
        filepath = self.project_root / filename
        if filepath.exists():
            self.checks_passed.append(f"✓ Found {description}: {filename}")
            return True
        else:
            self.checks_failed.append(f"✗ Missing {description}: {filename}")
            return False
    
    def check_directory_exists(self, dirname: str, description: str) -> bool:
        """Check if a directory exists"""
        dirpath = self.project_root / dirname
        if dirpath.is_dir():
            self.checks_passed.append(f"✓ Found {description}: {dirname}/")
            return True
        else:
            self.checks_failed.append(f"✗ Missing {description}: {dirname}/")
            return False
    
    def check_file_content(self, filename: str, required_content: str, description: str) -> bool:
        """Check if file contains specific content"""
        filepath = self.project_root / filename
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                if required_content in content:
                    self.checks_passed.append(f"✓ {description} contains required content")
                    return True
                else:
                    self.warnings.append(f"⚠ {description} missing required content: {required_content}")
                    return False
        except:
            self.checks_failed.append(f"✗ Cannot read {filename}")
            return False
    
    def validate_python_requirements(self) -> bool:
        """Validate Python requirements.txt"""
        print("\n[1] Validating Python Requirements...")
        
        filepath = self.project_root / "requirements.txt"
        if not filepath.exists():
            self.checks_failed.append("✗ requirements.txt not found")
            return False
        
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()
            
            # Check for critical packages
            content = ''.join(lines)
            required_packages = ['flask', 'pandas', 'numpy', 'requests', 'pydantic']
            
            missing = []
            for pkg in required_packages:
                if pkg not in content.lower():
                    missing.append(pkg)
            
            if missing:
                self.checks_failed.append(f"✗ requirements.txt missing packages: {missing}")
                return False
            else:
                self.checks_passed.append("✓ requirements.txt contains all critical packages")
            
            # Check numpy version compatibility
            for line in lines:
                if 'numpy' in line.lower():
                    if '1.24.0' in line or '1.23.' in line:
                        self.checks_failed.append("✗ numpy version incompatible with Python 3.12+. Update to >=1.26.0")
                        return False
                    else:
                        self.checks_passed.append("✓ numpy version compatible with Python 3.12+")
            
            return True
        except Exception as e:
            self.checks_failed.append(f"✗ Error validating requirements.txt: {e}")
            return False
    
    def validate_frontend_config(self) -> bool:
        """Validate frontend configuration"""
        print("\n[2] Validating Frontend Configuration...")
        
        checks = [
            ("package.json", "Frontend package configuration"),
            ("vite.config.ts", "Vite build configuration"),
            ("tsconfig.json", "TypeScript configuration"),
            ("public/", "Public assets directory"),
            ("src/", "Source code directory"),
        ]
        
        all_ok = True
        for filename, desc in checks:
            if filename.endswith('/'):
                if not self.check_directory_exists(filename, desc):
                    all_ok = False
            else:
                if not self.check_file_exists(filename, desc):
                    all_ok = False
        
        return all_ok
    
    def validate_backend_config(self) -> bool:
        """Validate backend configuration"""
        print("\n[3] Validating Backend Configuration...")
        
        checks = [
            ("app.py", "FastAPI application"),
            ("config.py", "Configuration file"),
            ("route_optimizer.py", "Route optimization engine"),
            ("database_manager.py", "Database manager"),
        ]
        
        all_ok = True
        for filename, desc in checks:
            if not self.check_file_exists(filename, desc):
                all_ok = False
        
        return all_ok
    
    def validate_docker_config(self) -> bool:
        """Validate Docker configuration"""
        print("\n[4] Validating Docker Configuration...")
        
        checks = [
            ("Dockerfile.backend", "Backend Dockerfile"),
            ("Dockerfile.frontend", "Frontend Dockerfile"),
            ("docker-compose.yml", "Docker Compose configuration"),
        ]
        
        all_ok = True
        for filename, desc in checks:
            if not self.check_file_exists(filename, desc):
                all_ok = False
        
        return all_ok
    
    def validate_environment_config(self) -> bool:
        """Validate environment configuration"""
        print("\n[5] Validating Environment Configuration...")
        
        checks = [
            (".env.example", "Environment variables template"),
            (".gitignore", "Git ignore file"),
        ]
        
        all_ok = True
        for filename, desc in checks:
            if not self.check_file_exists(filename, desc):
                all_ok = False
        
        return all_ok
    
    def validate_package_json(self) -> bool:
        """Validate package.json structure"""
        print("\n[6] Validating package.json...")
        
        try:
            with open(self.project_root / "package.json", 'r') as f:
                package = json.load(f)
            
            # Check required fields
            required_fields = ['name', 'version', 'scripts']
            for field in required_fields:
                if field not in package:
                    self.checks_failed.append(f"✗ package.json missing field: {field}")
                    return False
            
            # Check important scripts
            scripts = package.get('scripts', {})
            if 'build' not in scripts:
                self.warnings.append("⚠ package.json missing 'build' script")
            
            self.checks_passed.append("✓ package.json is valid")
            return True
        except Exception as e:
            self.checks_failed.append(f"✗ Error validating package.json: {e}")
            return False
    
    def validate_test_files(self) -> bool:
        """Validate test files exist"""
        print("\n[7] Validating Test Files...")
        
        checks = [
            ("test_comprehensive_vercel.py", "Comprehensive test suite"),
            ("requirements-test.txt", "Test dependencies"),
            ("pytest.ini", "Pytest configuration"),
        ]
        
        all_ok = True
        for filename, desc in checks:
            if not self.check_file_exists(filename, desc):
                all_ok = False
        
        return all_ok
    
    def validate_api_endpoints(self) -> bool:
        """Validate API endpoint configuration"""
        print("\n[8] Validating API Endpoint Configuration...")
        
        try:
            with open(self.project_root / "app.py", 'r') as f:
                content = f.read()
            
            required_endpoints = [
                '@app.get("/api/routes")',
                '@app.get("/health")',
                '@app.get("/status")',
            ]
            
            all_ok = True
            for endpoint in required_endpoints:
                if endpoint in content:
                    self.checks_passed.append(f"✓ Endpoint defined: {endpoint}")
                else:
                    self.warnings.append(f"⚠ Endpoint not found: {endpoint}")
                    all_ok = False
            
            return all_ok
        except Exception as e:
            self.checks_failed.append(f"✗ Cannot validate API endpoints: {e}")
            return False
    
    def validate_database_connectivity(self) -> bool:
        """Validate database configuration"""
        print("\n[9] Validating Database Connectivity...")
        
        try:
            with open(self.project_root / "config.py", 'r') as f:
                content = f.read()
            
            if 'DATABASE_URL' in content or 'DB_' in content:
                self.checks_passed.append("✓ Database configuration found in config.py")
                return True
            else:
                self.warnings.append("⚠ Database configuration may be incomplete")
                return False
        except Exception as e:
            self.checks_failed.append(f"✗ Cannot validate database config: {e}")
            return False
    
    def validate_route_generation_engine(self) -> bool:
        """Validate route generation engine is properly configured"""
        print("\n[10] Validating Route Generation Engine...")
        
        try:
            with open(self.project_root / "route_optimizer.py", 'r') as f:
                content = f.read()
            
            required_functions = [
                'generate_all_routes',
                '_find_direct_routes',
                '_find_single_transfer_routes',
                '_find_multi_transfer_routes',
                'pareto_optimize',
                'select_optimal_routes',
            ]
            
            all_ok = True
            for func in required_functions:
                if f'def {func}' in content:
                    self.checks_passed.append(f"✓ Route generation function found: {func}")
                else:
                    self.checks_failed.append(f"✗ Missing route generation function: {func}")
                    all_ok = False
            
            return all_ok
        except Exception as e:
            self.checks_failed.append(f"✗ Cannot validate route generation: {e}")
            return False
    
    def run_all_checks(self) -> int:
        """Run all validation checks"""
        print("=" * 80)
        print("VERCEL DEPLOYMENT VALIDATION")
        print("=" * 80)
        
        self.validate_python_requirements()
        self.validate_frontend_config()
        self.validate_backend_config()
        self.validate_docker_config()
        self.validate_environment_config()
        self.validate_package_json()
        self.validate_test_files()
        self.validate_api_endpoints()
        self.validate_database_connectivity()
        self.validate_route_generation_engine()
        
        # Print results
        print("\n" + "=" * 80)
        print("PASSED CHECKS:")
        print("=" * 80)
        for check in self.checks_passed:
            print(check)
        
        if self.checks_failed:
            print("\n" + "=" * 80)
            print("FAILED CHECKS (Must Fix):")
            print("=" * 80)
            for check in self.checks_failed:
                print(check)
        
        if self.warnings:
            print("\n" + "=" * 80)
            print("WARNINGS (Should Review):")
            print("=" * 80)
            for warning in self.warnings:
                print(warning)
        
        # Summary
        total = len(self.checks_passed) + len(self.checks_failed)
        passed = len(self.checks_passed)
        
        print("\n" + "=" * 80)
        print(f"FINAL RESULT: {passed}/{total} checks PASSED")
        print("=" * 80)
        
        if self.checks_failed:
            print("\n❌ DEPLOYMENT NOT READY - Fix failed checks above")
            return 1
        else:
            print("\n✅ DEPLOYMENT READY - All checks passed!")
            return 0


if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).parent)
    
    validator = VercelDeploymentValidator()
    exit_code = validator.run_all_checks()
    sys.exit(exit_code)
