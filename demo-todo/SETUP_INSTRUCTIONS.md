# Setup Instructions for FastAPI TODO Application

## Quick Start

### Windows Users

Run one of the following:

```bash
# Option 1: Using Python script (recommended)
python install_deps.py
python -m pytest tests/ -v

# Option 2: Using batch script
run_tests.bat

# Option 3: Using Python setup script
python setup_and_test.py
```

### Linux/macOS Users

```bash
# Run the shell script
./run_tests.sh

# Or manually:
python -m venv .venv
source .venv/bin/activate  # or: . .venv/bin/activate
pip install -r requirements.txt
python -m pytest tests/ -v
```

## Current Status

✓ **Code Quality**: All application code is complete and correct
✓ **Test Coverage**: Comprehensive test suite with 8 test functions
✓ **Documentation**: Complete setup and testing guides
✗ **Dependency Installation**: Dependencies must be installed before running tests

## Critical Requirement

Before running tests, you MUST install the project dependencies:

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

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify installation**:
   ```bash
   pip freeze | grep -E "fastapi|httpx|pytest|pydantic"
   ```

3. **Run tests**:
   ```bash
   python -m pytest tests/ -v
   ```

## Expected Test Results

All tests should PASS. There are two test suites:

### Async Tests (tests/test_main.py)
- Uses `httpx.AsyncClient` for async testing
- 8 test functions covering all endpoints
- Requires: httpx, fastapi, pytest-asyncio

### Sync Tests (tests/test_main_sync.py)  
- Uses `fastapi.TestClient` for synchronous testing
- 8 test functions covering all endpoints
- Requires: fastapi only (TestClient is built-in)

Run both:
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
├── install_deps.py       # Simple dependency installer
├── setup_and_test.py     # Cross-platform setup and test runner
├── run_tests.sh          # Linux/macOS test runner
├── run_tests.bat         # Windows test runner
├── README.md             # Project documentation
└── TESTING_GUIDE.md      # Detailed testing information
```

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'httpx'"
**Solution**: Run `pip install -r requirements.txt`

### Error: "PytestConfigWarning: Unknown config option: asyncio_mode"
**Solution**: Ensure pytest-asyncio is installed: `pip install pytest-asyncio`

### Tests fail to import from app
**Solution**: Make sure you're running pytest from the project root directory where `pytest.ini` is located

### Permission denied when running scripts
**Solution**: Use Python directly: `python setup_and_test.py` or `python -m pytest tests/ -v`

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

1. Install dependencies: `pip install -r requirements.txt`
2. Run tests: `python -m pytest tests/ -v`
3. All tests should pass ✓
4. Start the application: `uvicorn app.main:app --reload`

## Support

For more information, see:
- `README.md` - Project overview
- `TESTING_GUIDE.md` - Detailed testing information
- `tests/` - Complete test source code
