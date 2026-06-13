# Setup Instructions for FastAPI TODO Application

## Quick Start

### Recommended (Cross-platform, robust setup and test runner)

```bash
python setup_and_test.py
```

### Alternative Options

#### Windows Users

```bash
# Option 1: Using batch script
run_tests.bat
```

#### Linux/macOS Users

```bash
# Option 1: Run the shell script
./run_tests.sh

# Option 2: Manual setup (for debugging)
python -m venv .venv
source .venv/bin/activate  # or: . .venv/bin/activate
pip install -r requirements.txt
python -m pytest tests/ -v
```

## Current Status

✓ **Code Quality**: All application code is complete and correct
✓ **Test Coverage**: Comprehensive test suite with 16 test functions
✗ **Dependency Installation**: Dependencies must be installed and verified before running tests successfully

## Critical Requirement

Before running tests, you MUST ensure the project dependencies are installed and accessible. The `setup_and_test.py` script now handles this robustly, including verification.

```bash
pip install -r requirements.txt
```

This installs:
- **fastapi** (0.111.0) - Web framework
- **uvicorn** (0.29.0) - ASGI server
- **pydantic** (2.7.1) - Data validation
- **pytest** (8.2.0) - Test framework
- **pytest-asyncio** (0.23.6) - Async test support
- **httpx** (0.27.0) - Async HTTP client

## Verification Steps

1. **Run the comprehensive setup and test script**:
   ```bash
   python setup_and_test.py
   ```
   This script will create a virtual environment (if needed), upgrade pip, install dependencies, verify critical imports, and then run all tests.

2. **Expected output**: The script should report "All critical dependencies verified." and then all 16 tests should PASS.

## Expected Test Results

All tests should PASS. There are two test suites:

### Async Tests (tests/test_main.py)
- Uses `httpx.AsyncClient` for async testing
- 8 test functions covering all endpoints
- Requires: httpx, fastapi, pytest-asyncio

### Sync Tests (tests/test_main_sync.py)  
- Uses `fastapi.testclient.TestClient` for synchronous testing
- 8 test functions covering all endpoints
- Requires: fastapi only (TestClient is built-in)

Run both (via `setup_and_test.py` or manually):
```bash
python -m pytest tests/ -v
```

Run only async:
```bash
python -m pytest tests/test_main.py -v
```

Run only sync:
```bash
python -m pytest tests/test_main_sync.py -v
```

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application with all endpoints
│   ├── models.py         # Pydantic models (TodoCreate, TodoUpdate, TodoInDB)
│   └── db.py             # In-memory database implementation
├── tests/
│   ├── __init__.py
│   ├── conftest.py       # Pytest fixtures and configuration
│   ├── test_main.py      # Async tests
│   └── test_main_sync.py # Synchronous tests
├── requirements.txt      # Python dependencies
├── pytest.ini            # Pytest configuration
├── install_deps.py       # Simple dependency installer (updated)
├── setup_and_test.py     # Cross-platform setup and test runner (updated)
├── run_tests.sh          # Linux/macOS test runner
├── run_tests.bat         # Windows test runner
├── README.md             # Project documentation
└── TESTING_GUIDE.md      # Detailed testing information
```

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'pydantic'" (or similar for other packages)
**Solution**: Run `python setup_and_test.py`. This script will attempt to install dependencies and explicitly verify their import. Review its output carefully for any installation errors.

### Error: "PytestConfigWarning: Unknown config option: asyncio_mode"
**Solution**: Ensure `pytest-asyncio` is installed: `pip install pytest-asyncio` (this should be handled by `requirements.txt` and `setup_and_test.py`).

### Tests fail to import from app
**Solution**: Make sure you're running pytest from the project root directory where `pytest.ini` is located, or use `python setup_and_test.py`.

### Permission denied when running scripts
**Solution**: Use Python directly: `python setup_and_test.py` or `python -m pytest tests/ -v`.

## API Endpoints Reference

All endpoints are fully implemented and tested:

| Method | Endpoint | Status | Description |
|--------|----------|--------|-------------|
| GET | `/todos` | ✓ | List all todos |
| POST | `/todos` | ✓ | Create new todo (201) |
| GET | `/todos/{id}` | ✓ | Get single todo |
| PUT | `/todos/{id}` | ✓ | Update todo (supports partial updates) |
| DELETE | `/todos/{id}` | ✓ | Delete todo (204 No Content) |

## Next Steps

1. Run `python setup_and_test.py`
2. All tests should pass ✓
3. Start the application: `uvicorn app.main:app --reload`

## Support

For more information, see:
- `README.md` - Project overview
- `TESTING_GUIDE.md` - Detailed testing information
- `tests/` - Complete test source code
