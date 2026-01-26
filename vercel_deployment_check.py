#!/usr/bin/env python3
"""
Vercel Deployment Readiness Checker
Validates that the project is ready for Vercel deployment
"""

import os
import sys
import json
from pathlib import Path

def check_file_exists(path, description):
    """Check if a file exists"""
    exists = Path(path).exists()
    status = "✓" if exists else "✗"
    print(f"{status} {description}")
    return exists

def check_directory_exists(path, description):
    """Check if a directory exists"""
    exists = Path(path).is_dir()
    status = "✓" if exists else "✗"
    print(f"{status} {description}")
    return exists

def check_file_contains(path, search_string, description):
    """Check if a file contains a specific string"""
    try:
        with open(path, 'r') as f:
            content = f.read()
            found = search_string in content
            status = "✓" if found else "✗"
            print(f"{status} {description}")
            return found
    except:
        print(f"✗ {description} (file read error)")
        return False

def main():
    root = Path.cwd()
    print("\n🚀 Vercel Deployment Readiness Check\n")
    
    checks = [
        ("FRONTEND BUILD", [
            (lambda: check_file_exists("dist/index.html", "Frontend build output exists (dist/index.html)"),),
            (lambda: check_file_exists("dist/assets", "Frontend assets directory exists"),),
        ]),
        ("BACKEND CONFIGURATION", [
            (lambda: check_file_exists("api/index.py", "API serverless function exists"),),
            (lambda: check_file_exists("api/requirements.txt", "API requirements.txt exists"),),
        ]),
        ("VERCEL CONFIGURATION", [
            (lambda: check_file_exists("vercel.json", "vercel.json exists"),),
            (lambda: check_file_contains("vercel.json", "api/index.py", "vercel.json routes to api/index.py"),),
            (lambda: check_file_contains("vercel.json", "dist", "vercel.json outputDirectory is dist"),),
        ]),
        ("PACKAGE CONFIGURATION", [
            (lambda: check_file_exists("package.json", "package.json exists"),),
            (lambda: check_file_contains("package.json", "\"build\":", "package.json has build script"),),
        ]),
        ("GITIGNORE", [
            (lambda: check_file_exists(".vercelignore", ".vercelignore exists"),),
        ]),
        ("ENVIRONMENT SETUP", [
            (lambda: check_file_exists(".env", ".env file exists (for local development)"),),
        ]),
    ]
    
    all_passed = True
    for category, check_list in checks:
        print(f"\n📋 {category}")
        for check_func, in check_list:
            if not check_func():
                all_passed = False
    
    print("\n" + "="*50)
    
    if all_passed:
        print("\n✅ All checks passed! Ready for Vercel deployment.\n")
        print("📝 Next steps:")
        print("1. Push to GitHub repository")
        print("2. Connect repository to Vercel")
        print("3. Set environment variables in Vercel dashboard:")
        print("   - IRCTC_API_KEY")
        print("   - IRCTC_API_HOST")
        print("   - Any other required API keys")
        print("4. Vercel will automatically:")
        print("   - Run 'npm install --legacy-peer-deps'")
        print("   - Run 'npm run build'")
        print("   - Serve dist/ as static frontend")
        print("   - Run api/index.py as serverless function")
        return 0
    else:
        print("\n❌ Some checks failed. Please fix the issues above.\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
