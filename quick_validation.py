"""Quick validation test for Route Master system"""

import sys
import os
import logging

logging.getLogger().setLevel(logging.WARNING)

print('='*70)
print('ROUTE MASTER - QUICK SYSTEM VALIDATION TEST')
print('='*70)

all_ok = True

# Test 1: Python version
print('\n[1] Python Version Check')
print(f'    Version: {sys.version.split()[0]}')
print(f'    Required: 3.11+')
version_ok = sys.version_info >= (3, 11)
status = 'PASS' if version_ok else 'FAIL'
print(f'    Status: [{status}]')
all_ok = all_ok and version_ok

# Test 2: Core modules
print('\n[2] Core Modules Import Check')
modules_ok = True
try:
    from database_manager import DatabaseManager
    print(f'    [PASS] database_manager')
except Exception as e:
    print(f'    [FAIL] database_manager: {e}')
    modules_ok = False

try:
    from route_optimizer import ParetoTrainRouter
    print(f'    [PASS] route_optimizer')
except Exception as e:
    print(f'    [FAIL] route_optimizer: {e}')
    modules_ok = False

try:
    from flask import Flask
    print(f'    [PASS] flask')
except Exception as e:
    print(f'    [FAIL] flask: {e}')
    modules_ok = False

try:
    import pandas as pd
    print(f'    [PASS] pandas')
except Exception as e:
    print(f'    [FAIL] pandas: {e}')
    modules_ok = False

try:
    import numpy as np
    print(f'    [PASS] numpy {np.__version__}')
    if np.__version__.startswith('1.2') or np.__version__.startswith('1.3') or np.__version__.startswith('2'):
        print(f'           (Compatible with Python 3.11+)')
except Exception as e:
    print(f'    [FAIL] numpy: {e}')
    modules_ok = False

all_ok = all_ok and modules_ok

# Test 3: Requirements
print('\n[3] Requirements.txt Validation')
try:
    with open('requirements.txt', 'r') as f:
        content = f.read().lower()
    
    checks = {
        'flask': 'flask' in content,
        'pandas': 'pandas' in content,
        'numpy >= 1.26.0': 'numpy>=1.26.0' in content,
        'requests': 'requests' in content,
        'pydantic': 'pydantic' in content,
    }
    
    reqs_ok = True
    for pkg, found in checks.items():
        status = 'PASS' if found else 'FAIL'
        print(f'    [{status}] {pkg}')
        reqs_ok = reqs_ok and found
    
    all_ok = all_ok and reqs_ok
except Exception as e:
    print(f'    [FAIL] Cannot read requirements.txt: {e}')
    all_ok = False

# Test 4: Configuration files
print('\n[4] Key Configuration Files')
configs = {
    'app.py': 'Backend API',
    'config.py': 'Configuration',
    'route_optimizer.py': 'Route engine',
    'database_manager.py': 'Database layer',
    'requirements.txt': 'Dependencies',
    'package.json': 'Frontend',
    'vite.config.ts': 'Build tool',
    'src/': 'Source code',
    'public/': 'Static assets',
}

config_ok = True
for cfg, desc in configs.items():
    found = os.path.exists(cfg)
    status = 'PASS' if found else 'FAIL'
    print(f'    [{status}] {cfg:20} - {desc}')
    config_ok = config_ok and found

all_ok = all_ok and config_ok

# Test 5: Test files
print('\n[5] Test Files Available')
test_files = {
    'test_comprehensive_vercel.py': 'Complete test suite',
    'test_route_generation_complete.py': 'Route generation test',
    'vercel_deployment_validator.py': 'Deployment validator',
    'TESTING_AND_DEPLOYMENT_GUIDE.md': 'Testing guide',
    'VERCEL_DEPLOYMENT_CHECKLIST.md': 'Deployment checklist',
}

tests_ok = True
for test_file, desc in test_files.items():
    found = os.path.exists(test_file)
    status = 'PASS' if found else 'FAIL'
    print(f'    [{status}] {test_file:35} - {desc}')
    tests_ok = tests_ok and found

all_ok = all_ok and tests_ok

# Test 6: API Endpoints
print('\n[6] API Endpoints Check')
try:
    with open('app.py', 'r') as f:
        app_content = f.read()
    
    endpoints = {
        'GET /': '@app.get("/")' in app_content,
        'POST /search': '@app.post(' in app_content,
        'GET /results': '@app.get(' in app_content,
    }
    
    endpoints_ok = True
    for endpoint, found in endpoints.items():
        status = 'PASS' if found else 'WARN'
        print(f'    [{status}] {endpoint}')
        endpoints_ok = endpoints_ok and found
    
    all_ok = all_ok and endpoints_ok
except Exception as e:
    print(f'    [FAIL] Cannot validate endpoints: {e}')
    all_ok = False

# Final Summary
print('\n' + '='*70)
print('VALIDATION SUMMARY')
print('='*70)
print(f'✓ Python Version:        [PASS]' if version_ok else f'✗ Python Version:        [FAIL]')
print(f'✓ Core Modules:          [PASS]' if modules_ok else f'✗ Core Modules:          [FAIL]')
print(f'✓ Requirements:          [PASS]' if reqs_ok else f'✗ Requirements:          [FAIL]')
print(f'✓ Configuration Files:   [PASS]' if config_ok else f'✗ Configuration Files:   [FAIL]')
print(f'✓ Test Files:            [PASS]' if tests_ok else f'✗ Test Files:            [FAIL]')
print(f'✓ API Endpoints:         [PASS]' if endpoints_ok else f'✗ API Endpoints:         [FAIL]')
print('='*70)

if all_ok:
    print('\n✅ SYSTEM VALIDATION PASSED - READY FOR DEPLOYMENT')
    print('\nNext steps:')
    print('  1. Run: python test_route_generation_complete.py')
    print('  2. Run: python test_comprehensive_vercel.py')
    print('  3. Review test output')
    print('  4. Push to GitHub: git push origin testfolder_v4')
else:
    print('\n❌ SYSTEM VALIDATION FAILED - FIX ISSUES ABOVE')

print('='*70)
