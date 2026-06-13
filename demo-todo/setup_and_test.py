#!/usr/bin/env python
"""Setup script to create venv, install dependencies, and run tests."""

import subprocess
import sys
import venv
import os
from pathlib import Path

def main():
    project_root = Path(__file__).parent
    venv_dir = project_root / ".venv"

    # Step 1: Create virtual environment if it doesn't exist
    if not venv_dir.exists():
        print("Creating virtual environment...")
        venv.create(venv_dir, with_pip=True)
        print(f"Virtual environment created at {venv_dir}")

    # Determine Python executable path based on OS
    if sys.platform == "win32":
        python_exe = venv_dir / "Scripts" / "python.exe"
        pip_exe = venv_dir / "Scripts" / "pip.exe"
    else:
        python_exe = venv_dir / "bin" / "python"
        pip_exe = venv_dir / "bin" / "pip"

    # Ensure pip is up-to-date within the virtual environment
    print("Upgrading pip...")
    result = subprocess.run(
        [str(python_exe), "-m", "pip", "install", "--upgrade", "pip"],
        cwd=project_root
    )
    if result.returncode != 0:
        print("Failed to upgrade pip")
        return 1

    # Step 2: Install dependencies
    print("Installing dependencies...")
    requirements_file = project_root / "requirements.txt"
    result = subprocess.run(
        [str(pip_exe), "install", "-r", str(requirements_file)],
        cwd=project_root
    )

    if result.returncode != 0:
        print("Failed to install dependencies")
        return 1

    print("Dependencies installed successfully")

    # Step 3: Verify critical imports using the venv's python
    print("\nVerifying critical imports...")
    critical_packages = ["pydantic", "fastapi", "httpx", "pytest", "pytest_asyncio"]
    for pkg in critical_packages:
        print(f"  Checking '{pkg}'...")
        # Use the venv's python to try importing the package
        import_check_command = [
            str(python_exe),
            "-c",
            f"import {pkg}; print(f'✓ {pkg} imported successfully')"
        ]
        check_result = subprocess.run(
            import_check_command,
            cwd=project_root,
            capture_output=True,
            text=True
        )
        if check_result.returncode != 0:
            print(f"✗ {pkg} import failed. Output:\n{check_result.stderr}")
            print("Dependency verification failed. Exiting.")
            return 1
        else:
            print(check_result.stdout.strip())

    print("All critical dependencies verified.")

    # Step 4: Run tests
    print("\nRunning tests...")
    test_result = subprocess.run(
        [str(python_exe), "-m", "pytest", "tests/", "-v"],
        cwd=project_root
    )

    return test_result.returncode

if __name__ == "__main__":
    sys.exit(main())
