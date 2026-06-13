#!/usr/bin/env python3
"""
Simple dependency installation script.
This script installs all required packages from requirements.txt to the current Python environment.
"""

import subprocess
import sys

def install_dependencies():
    """Install dependencies using pip."""
    print("Installing dependencies from requirements.txt...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        capture_output=False
    )
    return result.returncode == 0

def verify_imports():
    """Verify that critical packages are installed."""
    packages = ["fastapi", "uvicorn", "pydantic", "pytest", "pytest_asyncio", "httpx"]
    missing = []

    for package in packages:
        try:
            __import__(package)
            print(f"✓ {package} is installed")
        except ImportError:
            print(f"✗ {package} is NOT installed")
            missing.append(package)

    return len(missing) == 0

if __name__ == "__main__":
    print("FastAPI TODO Project - Dependency Installation")
    print("=" * 50)

    if install_dependencies():
        print("\nDependencies installed successfully!")

        print("\nVerifying imports...")
        if verify_imports():
            print("\n✓ All dependencies are available!")
            sys.exit(0)
        else:
            print("\n✗ Some dependencies are missing")
            sys.exit(1)
    else:
        print("\n✗ Failed to install dependencies")
        sys.exit(1)
