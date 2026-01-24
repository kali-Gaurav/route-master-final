#!/usr/bin/env python
"""Test API with detailed error logging"""

import requests
import subprocess
import sys
import time

BASE_URL = "http://127.0.0.1:5000"

def main():
    print("Starting API server with error capture...")
    
    # Start API and capture output
    proc = subprocess.Popen(
        [sys.executable, 'api.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    print("Waiting 15 seconds for API to start...")
    time.sleep(15)
    
    print("\n[*] Making test request to /api/routes...")
    try:
        params = {
            'origin': 'NDLS',
            'destination': 'KOTA',
            'max_transfers': 1,
            'date': '25-01-2026'
        }
        resp = requests.get(f"{BASE_URL}/api/routes", params=params, timeout=60)
        print(f"Response Status: {resp.status_code}")
        print(f"Response body: {resp.text[:1000]}")
    except Exception as e:
        print(f"Request error: {e}")
    
    # Wait a bit and check output
    time.sleep(2)
    
    print("\n[*] API Server Output:")
    print("=" * 80)
    
    try:
        proc.terminate()
        stdout, _ = proc.communicate(timeout=5)
        # Print last 100 lines
        lines = stdout.split('\n')
        for line in lines[-100:]:
            if line:
                print(line)
    except Exception as e:
        print(f"Error getting output: {e}")
        try:
            proc.kill()
        except:
            pass

if __name__ == "__main__":
    main()
