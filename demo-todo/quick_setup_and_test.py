#!/usr/bin/env python3
"""
Quick setup and test script for the TODO FastAPI application.
This script sets up a virtual environment, installs dependencies, and runs tests.
Provides detailed diagnostics if anything goes wrong.
"""

import subprocess
import sys
import venv
import os
from pathlib import Path


def run_command(cmd, description, show_output=False):
    """Run a command and return True if successful."""
    print(f"\n{'=' * 60}")
    print(f"📌 {description}")
    print(f"{'=' * 60}")
    print(f"Running: {' '.join(cmd)}\n")

    result = subprocess.run(
        cmd,
        capture_output=not show_output,
        text=True
    )

    if result.returncode != 0:
        print(f"❌ FAILED")
        if result.stderr:
            print(f"Error output:\n{result.stderr}")
        if result.stdout:
            print(f"Standard output:\n{result.stdout}")
        return False

    if show_output:
        if result.stdout:
            print(result.stdout)
    else:
        print(f"✅ SUCCESS")
    return True


def main():
    print("=" * 60)
    print("🚀 FastAPI TODO Application - Setup & Test Script")
    print("=" * 60)

    project_root = Path(__file__).parent
    venv_dir = project_root / ".venv"

    # Determine Python executable paths
    if sys.platform == "win32":
        python_exe = venv_dir / "Scripts" / "python.exe"
        pip_exe = venv_dir / "Scripts" / "pip.exe"
    else:
        python_exe = venv_dir / "bin" / "python"
        pip_exe = venv_dir / "bin" / "pip"

    print(f"\n📁 Project root: {project_root}")
    print(f"🐍 Virtual environment: {venv_dir}")
    print(f"📦 Python executable: {python_exe}")
    print(f"📦 Pip executable: {pip_exe}")

    # Step 1: Create virtual environment
    if venv_dir.exists():
        print(f"\n✅ Virtual environment already exists at {venv_dir}")
    else:
        print(f"\n📝 Creating virtual environment...")
        venv.create(venv_dir, with_pip=True)
        print(f"✅ Virtual environment created")

    # Step 2: Upgrade pip
    if not run_command(
        [str(python_exe), "-m", "pip", "install", "--upgrade", "pip"],
        "Step 1: Upgrading pip"
    ):
        return 1

    # Step 3: Install dependencies
    requirements_file = project_root / "requirements.txt"
    if not run_command(
        [str(pip_exe), "install", "-r", str(requirements_file)],
        "Step 2: Installing dependencies from requirements.txt"
    ):
        return 1

    # Step 4: Verify imports
    print(f"\n{'=' * 60}")
    print("📌 Step 3: Verifying critical packages")
    print(f"{'=' * 60}")

    critical_packages = ["pydantic", "fastapi", "httpx", "pytest", "pytest_asyncio"]
    all_verified = True

    for pkg in critical_packages:
        check_cmd = [
            str(python_exe),
            "-c",
            f"import {pkg}; print(f'✓ {{pkg}} version ' + {pkg}.__version__)"
        ]
        result = subprocess.run(check_cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✅ {result.stdout.strip()}")
        else:
            print(f"❌ Failed to import '{pkg}'")
            all_verified = False

    if not all_verified:
        print("\n⚠️  Some packages failed to import. Check the errors above.")
        return 1

    # Step 5: Run tests
    print(f"\n{'=' * 60}")
    print("📌 Step 4: Running tests")
    print(f"{'=' * 60}\n")

    test_result = subprocess.run(
        [str(python_exe), "-m", "pytest", "tests/", "-v", "--tb=short"],
        cwd=project_root,
        capture_output=False
    )

    if test_result.returncode == 0:
        print(f"\n{'=' * 60}")
        print("✅ ALL TESTS PASSED!")
        print(f"{'=' * 60}")
        return 0
    else:
        print(f"\n{'=' * 60}")
        print("❌ TESTS FAILED")
        print(f"{'=' * 60}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
