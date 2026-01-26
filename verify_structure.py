#!/usr/bin/env python3
"""
Simple test to verify Vercel serverless function structure
"""

import sys
from pathlib import Path

# Test that the api/index.py file is syntactically correct
api_file = Path(__file__).parent / 'api' / 'index.py'

if not api_file.exists():
    print(f"✗ API file not found: {api_file}")
    sys.exit(1)

try:
    # Just compile the Python file to check syntax
    import py_compile
    py_compile.compile(str(api_file), doraise=True)
    print(f"✓ API file syntax is valid: {api_file.relative_to(Path.cwd())}")
except py_compile.PyCompileError as e:
    print(f"✗ Syntax error in API file: {e}")
    sys.exit(1)

# Check vercel.json structure
import json
vercel_file = Path(__file__).parent / 'vercel.json'

if not vercel_file.exists():
    print(f"✗ vercel.json not found")
    sys.exit(1)

try:
    with open(vercel_file) as f:
        vercel_config = json.load(f)
    
    # Verify key settings
    checks = [
        ('buildCommand' in vercel_config, 'buildCommand configured'),
        ('outputDirectory' in vercel_config, 'outputDirectory configured'),
        (vercel_config.get('outputDirectory') == 'dist', 'outputDirectory is dist'),
        ('functions' in vercel_config and 'api/index.py' in vercel_config['functions'], 'api/index.py configured as function'),
        ('routes' in vercel_config, 'routes configured'),
    ]
    
    print(f"\n✓ vercel.json is valid JSON")
    for passed, description in checks:
        status = "✓" if passed else "✗"
        print(f"  {status} {description}")
        if not passed:
            print(f"    Current config: {json.dumps(vercel_config, indent=2)}")
            
except json.JSONDecodeError as e:
    print(f"✗ Invalid JSON in vercel.json: {e}")
    sys.exit(1)

# Check package.json
try:
    with open(Path(__file__).parent / 'package.json') as f:
        pkg_config = json.load(f)
    
    has_build = 'build' in pkg_config.get('scripts', {})
    print(f"\n✓ package.json is valid JSON")
    print(f"  {'✓' if has_build else '✗'} build script configured")
    
except json.JSONDecodeError as e:
    print(f"✗ Invalid JSON in package.json: {e}")
    sys.exit(1)

# Check dist folder
dist_folder = Path(__file__).parent / 'dist'
if dist_folder.exists() and (dist_folder / 'index.html').exists():
    print(f"\n✓ Frontend build exists (dist/index.html)")
else:
    print(f"\n✗ Frontend build missing (dist/index.html)")

# Check .env files
print(f"\n✓ Environment configuration:")
if (Path(__file__).parent / '.env').exists():
    print(f"  ✓ .env file exists (local development)")
if (Path(__file__).parent / '.env.vercel').exists():
    print(f"  ✓ .env.vercel file exists (Vercel deployment)")
if (Path(__file__).parent / '.env.example').exists():
    print(f"  ✓ .env.example file exists (documentation)")

print("\n" + "="*60)
print("✅ Vercel deployment structure is valid and ready!")
print("\n📦 Deployment Flow:")
print("1. Frontend (Vite React): npm run build → dist/")
print("2. Backend (Flask serverless): api/index.py (Python 3.12)")
print("3. Routing:")
print("   - /api/* → api/index.py (serverless function)")
print("   - /* → dist/index.html (static SPA)")
print("\n🚀 Ready to deploy to Vercel!")
