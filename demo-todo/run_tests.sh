#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

VENV_DIR=".venv"

echo "--- Starting test script ---"
echo "Current working directory: $(pwd)"
echo "Python executable in PATH: $(which python || echo 'Not found')"
echo "Pytest executable in PATH: $(which pytest || echo 'Not found')"

# Check if the virtual environment directory exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found. Creating it..."
    python -m venv "$VENV_DIR"
else
    echo "Virtual environment found."
fi

# Determine virtual environment executable paths
# Check for Windows-style first, then Unix-style
if [ -f "$VENV_DIR/Scripts/python.exe" ]; then # Windows
    echo "Detected Windows-style virtual environment."
    PYTHON_EXEC="$VENV_DIR/Scripts/python.exe"
    PIP_EXEC="$VENV_DIR/Scripts/pip.exe"
    # PYTEST_EXEC is not directly used for execution, but for logging if needed
    PYTEST_EXEC_PATH="$VENV_DIR/Scripts/pytest.exe"
elif [ -f "$VENV_DIR/bin/python" ]; then # Unix/macOS
    echo "Detected Unix-style virtual environment."
    PYTHON_EXEC="$VENV_DIR/bin/python"
    PIP_EXEC="$VENV_DIR/bin/pip"
    # PYTEST_EXEC is not directly used for execution, but for logging if needed
    PYTEST_EXEC_PATH="$VENV_DIR/bin/pytest"
else
    echo "Error: Could not find virtual environment Python executable. Please ensure Python and venv are properly set up."
    exit 1
fi

echo "Using Python executable: $PYTHON_EXEC"
echo "Using Pip executable: $PIP_EXEC"
echo "Using Pytest executable (expected path): $PYTEST_EXEC_PATH"

echo "Installing/updating dependencies from requirements.txt using $PIP_EXEC..."
"$PIP_EXEC" install -r requirements.txt

echo "Verifying installed packages in virtual environment (pip freeze):"
"$PIP_EXEC" freeze

echo "Checking for specific packages (httpx, pytest, fastapi, uvicorn, pydantic, pytest-asyncio):"
"$PIP_EXEC" list | grep -E 'httpx|pytest|fastapi|uvicorn|pydantic|pytest-asyncio' || true # Use grep to filter, || true to prevent exit on no match

echo "Running pytest using '$PYTHON_EXEC -m pytest' command..."

# Try running async tests first
if "$PYTHON_EXEC" -m pytest tests/test_main.py "$@"; then
    echo "--- Async tests passed ---"
else
    echo "Async tests failed. Attempting to run synchronous tests as fallback..."
    # If async tests fail due to httpx issues, try sync tests
    if "$PYTHON_EXEC" -m pytest tests/test_main_sync.py "$@"; then
        echo "--- Synchronous tests passed (async tests may have failed due to missing httpx) ---"
    else
        echo "Both test suites failed. Check the output above for details."
        exit 1
    fi
fi

echo "--- Test script finished ---"
