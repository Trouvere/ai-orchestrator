@echo off
REM Windows batch script to set up virtual environment and run tests

setlocal enabledelayedexpansion

echo --- Starting test setup and execution on Windows ---
echo Current directory: %cd%

REM Define venv directory
set "VENV_DIR=.venv"

REM Check if virtual environment exists
if not exist "%VENV_DIR%" (
    echo Creating virtual environment at %VENV_DIR%...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo Failed to create virtual environment
        exit /b 1
    )
) else (
    echo Virtual environment found at %VENV_DIR%
)

REM Set paths for Windows
set "PYTHON_EXEC=%VENV_DIR%\Scripts\python.exe"
set "PIP_EXEC=%VENV_DIR%\Scripts\pip.exe"
set "PYTEST_EXEC=%VENV_DIR%\Scripts\pytest.exe"

echo Using Python executable: %PYTHON_EXEC%
echo Using Pip executable: %PIP_EXEC%

REM Install/update dependencies
echo Installing dependencies from requirements.txt...
"%PIP_EXEC%" install -r requirements.txt
if errorlevel 1 (
    echo Failed to install dependencies
    exit /b 1
)

REM Verify installed packages
echo.
echo Verifying installed packages:
"%PIP_EXEC%" freeze | findstr /I "httpx pytest fastapi uvicorn pydantic pytest-asyncio"

REM Run tests
echo.
echo Running tests...
"%PYTHON_EXEC%" -m pytest tests/ -v
if errorlevel 1 (
    echo Tests failed
    exit /b 1
)

echo.
echo --- Tests completed successfully ---
exit /b 0
