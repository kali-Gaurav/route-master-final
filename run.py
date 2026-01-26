#!/usr/bin/env python
"""
Unified Run Script for FINALTrip Railway Router

Launches both FastAPI backend and Vite frontend simultaneously for development.

Usage:
    python run.py                    # Run both backend and frontend
    python run.py --backend-only     # Run only the backend API
    python run.py --frontend-only    # Run only the Vite dev server
"""

import sys
import subprocess
import time
import os
from pathlib import Path
import argparse

class UnifiedRunner:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.backend_port = 5000
        self.frontend_port = 5173
    
    def run_backend(self):
        """Start FastAPI backend server"""
        print(f"[BACKEND] Starting FastAPI server on port {self.backend_port}...")
        try:
            cmd = [
                sys.executable,
                "-m", "uvicorn",
                "api_v2:app",
                "--host", "0.0.0.0",
                "--port", str(self.backend_port),
                "--log-level", "info"
            ]
            
            backend_process = subprocess.Popen(
                cmd,
                cwd=str(self.base_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            print(f"[BACKEND] Backend server started with PID {backend_process.pid}")
            return backend_process
        except Exception as e:
            print(f"[BACKEND] ERROR: Failed to start backend: {e}")
            return None
    
    def run_frontend(self):
        """Start Vite frontend dev server"""
        print(f"[FRONTEND] Starting Vite dev server on port {self.frontend_port}...")
        try:
            # Check if npm is available
            subprocess.run(["npm", "--version"], capture_output=True, check=True)
            
            cmd = ["npm", "run", "dev"]
            
            frontend_process = subprocess.Popen(
                cmd,
                cwd=str(self.base_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            print(f"[FRONTEND] Frontend dev server started with PID {frontend_process.pid}")
            return frontend_process
        except FileNotFoundError:
            print("[FRONTEND] ERROR: npm not found. Please install Node.js")
            return None
        except Exception as e:
            print(f"[FRONTEND] ERROR: Failed to start frontend: {e}")
            return None
    
    def run_both(self):
        """Run both backend and frontend"""
        print("\n" + "="*80)
        print("FINALTRIP RAILWAY ROUTER - UNIFIED DEVELOPMENT SERVER".center(80))
        print("="*80 + "\n")
        
        backend = self.run_backend()
        time.sleep(2)
        frontend = self.run_frontend()
        
        if backend and frontend:
            print("\n" + "="*80)
            print("BOTH SERVERS RUNNING".center(80))
            print("="*80)
            print(f"Backend:  http://localhost:{self.backend_port}")
            print(f"Frontend: http://localhost:{self.frontend_port}")
            print("\nPress Ctrl+C to stop both servers...\n")
            
            try:
                backend.wait()
                frontend.wait()
            except KeyboardInterrupt:
                print("\n[SHUTDOWN] Stopping servers...")
                backend.terminate()
                frontend.terminate()
                time.sleep(1)
                backend.kill()
                frontend.kill()
                print("[SHUTDOWN] Servers stopped")
        else:
            print("[ERROR] Failed to start one or both servers")
            if backend:
                backend.terminate()
            if frontend:
                frontend.terminate()
            sys.exit(1)
    
    def run_backend_only(self):
        """Run only backend"""
        print("\n" + "="*80)
        print("FINALTRIP - BACKEND ONLY".center(80))
        print("="*80 + "\n")
        
        backend = self.run_backend()
        
        if backend:
            print(f"\nBackend running at http://localhost:{self.backend_port}")
            print("Press Ctrl+C to stop...\n")
            
            try:
                backend.wait()
            except KeyboardInterrupt:
                print("\n[SHUTDOWN] Stopping backend...")
                backend.terminate()
                backend.wait()
                print("[SHUTDOWN] Backend stopped")
        else:
            sys.exit(1)
    
    def run_frontend_only(self):
        """Run only frontend"""
        print("\n" + "="*80)
        print("FINALTRIP - FRONTEND ONLY".center(80))
        print("="*80 + "\n")
        
        frontend = self.run_frontend()
        
        if frontend:
            print(f"\nFrontend running at http://localhost:{self.frontend_port}")
            print("Press Ctrl+C to stop...\n")
            
            try:
                frontend.wait()
            except KeyboardInterrupt:
                print("\n[SHUTDOWN] Stopping frontend...")
                frontend.terminate()
                frontend.wait()
                print("[SHUTDOWN] Frontend stopped")
        else:
            sys.exit(1)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='FINALTrip Railway Router - Unified Development Server')
    parser.add_argument('--backend-only', action='store_true', help='Run only backend API')
    parser.add_argument('--frontend-only', action='store_true', help='Run only frontend')
    
    args = parser.parse_args()
    
    runner = UnifiedRunner()
    
    if args.backend_only:
        runner.run_backend_only()
    elif args.frontend_only:
        runner.run_frontend_only()
    else:
        runner.run_both()

if __name__ == "__main__":
    main()
