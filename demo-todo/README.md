# Todo List FastAPI Application

This is a simple REST API for managing todo items, built with FastAPI.

## Features

*   **Create Todo**: Add new todo items with a title, optional description, and completion status.
*   **Get All Todos**: Retrieve a list of all existing todo items.
*   **Get Todo by ID**: Retrieve a single todo item by its unique identifier.
*   **Update Todo**: Modify existing todo items (partial updates supported).
*   **Delete Todo**: Remove todo items.

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py       # FastAPI application and endpoints
│   ├── models.py     # Pydantic models for Todo items
│   └── db.py         # In-memory database simulation
├── tests/
│   ├── __init__.py
│   └── test_main.py  # Pytest tests for the API
├── .gitignore        # Git ignore file
├── README.md         # Project README
├── requirements.txt  # Python dependencies
└── run_tests.sh      # Script to install dependencies and run tests
```

## Setup and Installation

1.  **Clone the repository** (if applicable, for a real project):
    ```bash
    # git clone <repository-url>
    # cd todo-fastapi
    ```

2.  **For running the application locally (manual setup):**
    a.  **Create a virtual environment** (recommended):
        ```bash
        python -m venv .venv
        source .venv/bin/activate  # On Windows: .venv\Scripts\activate
        ```
    b.  **Install dependencies**:
        ```bash
        pip install -r requirements.txt
        ```
    *(Note: For running tests, the `run_tests.sh` script handles virtual environment creation and dependency installation automatically.)*

## Running the Application

To run the FastAPI application using Uvicorn:

```bash
.venv/bin/uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.
You can access the interactive API documentation (Swagger UI) at `http://127.0.0.1:8000/docs`.

## API Endpoints

*   **`GET /todos`**: Retrieve all todo items.
*   **`POST /todos`**: Create a new todo item.
    *   Request Body (JSON): `{"title": "string", "description": "string", "completed": boolean}`
*   **`GET /todos/{id}`**: Retrieve a specific todo item by its ID.
*   **`PUT /todos/{id}`**: Update an existing todo item by its ID.
    *   Request Body (JSON): `{"title": "string", "description": "string", "completed": boolean}` (all fields optional for partial update)
*   **`DELETE /todos/{id}`**: Delete a todo item by its ID.

## Running Tests

### Option 1: Using the automated test script (Recommended for shell environments)

```bash
chmod +x run_tests.sh # Make the script executable if it isn't already
./run_tests.sh
```

This script will automatically create a virtual environment (if it doesn't exist), activate it, install/update dependencies from `requirements.txt`, and then execute all tests.

### Option 2: Using Windows batch script

```bash
run_tests.bat
```

This batch script (Windows only) creates a virtual environment, installs dependencies, and runs the tests.

### Option 3: Using Python setup script

```bash
python setup_and_test.py
```

This script creates a virtual environment, installs dependencies, and runs the tests (works on all platforms).

### Option 4: Manual setup (requires python 3.10+)

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run async tests (with httpx)
python -m pytest tests/test_main.py -v

# Or run synchronous tests (without httpx dependency)
python -m pytest tests/test_main_sync.py -v

# Or run all tests
python -m pytest tests/ -v
```

### Test Variants

- **`tests/test_main.py`**: Async tests using `httpx.AsyncClient` (requires httpx installation)
- **`tests/test_main_sync.py`**: Synchronous tests using `fastapi.testclient.TestClient` (no additional dependencies beyond FastAPI)

## Technologies Used

*   [FastAPI](https://fastapi.tiangolo.com/)
*   [Pydantic](https://pydantic-docs.helpmanual.io/)
*   [Uvicorn](https://www.uvicorn.org/)
*   [Pytest](https://docs.pytest.org/)
*   [Httpx](https://www.python-httpx.org/)
