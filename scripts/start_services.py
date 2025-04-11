#!/usr/bin/env python3
import subprocess
import sys
import os
import signal
import time
from pathlib import Path
import shutil

# Get project root directory
project_root = Path(__file__).parent.parent

# Store processes to manage their lifecycle
processes = []

def check_environment():
    """Check if all required tools are installed"""
    # Check Python packages
    try:
        import fastapi
        import uvicorn
        import httpx
    except ImportError as e:
        print(f"Missing Python package: {e.name}")
        print("Please run: pip install -r requirements.txt")
        return False

    # Check Node.js
    if not shutil.which('npm'):
        print("Node.js/npm not found. Please install Node.js")
        return False

    return True

def start_backend():
    """Start the FastAPI backend server"""
    print("Starting backend server...")
    try:
        backend_process = subprocess.Popen(
            ["uvicorn", "backend.main:app", "--reload", "--port", "8000"],
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        processes.append(("Backend", backend_process))
        
        # Check for immediate startup errors
        time.sleep(2)
        if backend_process.poll() is not None:
            _, stderr = backend_process.communicate()
            print(f"Backend failed to start:\n{stderr}")
            return False
        return True
    except Exception as e:
        print(f"Error starting backend: {str(e)}")
        return False

def start_ml_server():
    """Start the ML server"""
    print("Starting ML server...")
    try:
        # Add ml_server to Python path
        env = os.environ.copy()
        env["PYTHONPATH"] = str(project_root)
        
        ml_process = subprocess.Popen(
            ["uvicorn", "ml_server.main:app", "--reload", "--port", "8001"],
            cwd=project_root,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        processes.append(("ML Server", ml_process))
        
        # Check for immediate startup errors
        time.sleep(2)
        if ml_process.poll() is not None:
            _, stderr = ml_process.communicate()
            print(f"ML server failed to start:\n{stderr}")
            return False
        return True
    except Exception as e:
        print(f"Error starting ML server: {str(e)}")
        return False

def start_frontend():
    """Start the Next.js frontend"""
    print("Starting frontend...")
    try:
        frontend_process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=project_root / "frontend",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        processes.append(("Frontend", frontend_process))
        
        # Check for immediate startup errors
        time.sleep(2)
        if frontend_process.poll() is not None:
            _, stderr = frontend_process.communicate()
            print(f"Frontend failed to start:\n{stderr}")
            return False
        return True
    except Exception as e:
        print(f"Error starting frontend: {str(e)}")
        return False

def cleanup(signum, frame):
    """Clean up processes on exit"""
    print("\nShutting down services...")
    for name, process in processes:
        if process.poll() is None:  # If process is still running
            print(f"Stopping {name}...")
            process.terminate()
            try:
                process.wait(timeout=5)  # Wait up to 5 seconds for graceful shutdown
            except subprocess.TimeoutExpired:
                print(f"Force killing {name}...")
                process.kill()
    sys.exit(0)

def main():
    # Check environment first
    if not check_environment():
        sys.exit(1)

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:
        # Start all services
        if not start_backend():
            cleanup(None, None)
            return
        
        if not start_ml_server():
            cleanup(None, None)
            return
            
        if not start_frontend():
            cleanup(None, None)
            return

        print("\nAll services started!")
        print("Frontend: http://localhost:3000")
        print("Backend API: http://localhost:8000")
        print("ML Server: http://localhost:8001")
        print("\nPress Ctrl+C to stop all services\n")

        # Keep the script running and monitor child processes
        while True:
            for name, process in processes:
                if process.poll() is not None:
                    _, stderr = process.communicate()
                    print(f"\n{name} process exited unexpectedly!")
                    print(f"Error output:\n{stderr}")
                    cleanup(None, None)
            time.sleep(1)

    except Exception as e:
        print(f"Error starting services: {str(e)}")
        cleanup(None, None)
        sys.exit(1)

if __name__ == "__main__":
    main() 