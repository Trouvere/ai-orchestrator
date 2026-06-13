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

    # Step 3: Run tests
    print("\nRunning tests...")
    test_result = subprocess.run(
        [str(python_exe), "-m", "pytest", "tests/", "-v"],
        cwd=project_root
    )

    return test_result.returncode

if __name__ == "__main__":
    sys.exit(main())
