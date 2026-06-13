"""Alternative test suite using synchronous TestClient from FastAPI."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_get_empty_todos(client):
    response = client.get("/todos")
    assert response.status_code == 200
    assert response.json() == []


def test_create_todo(client):
    response = client.post(
        "/todos",
        json={"title": "Buy groceries", "description": "Milk, Eggs, Bread"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Buy groceries"
    assert data["description"] == "Milk, Eggs, Bread"
    assert data["completed"] is False
    assert "id" in data

    # Verify it's in the list
    response = client.get("/todos")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Buy groceries"


def test_get_single_todo(client):
    # First create a todo
    post_response = client.post(
        "/todos",
        json={"title": "Read a book"}
    )
    todo_id = post_response.json()["id"]

    # Then get it
    get_response = client.get(f"/todos/{todo_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == todo_id
    assert data["title"] == "Read a book"
    assert data["completed"] is False

    # Test non-existent todo
    not_found_response = client.get("/todos/999")
    assert not_found_response.status_code == 404
    assert not_found_response.json() == {"detail": "Todo not found"}


def test_update_todo(client):
    # Create a todo
    post_response = client.post(
        "/todos",
        json={"title": "Walk the dog", "completed": False}
    )
    todo_id = post_response.json()["id"]

    # Update it
    put_response = client.put(
        f"/todos/{todo_id}",
        json={"title": "Walk the cat", "completed": True, "description": "New description"}
    )
    assert put_response.status_code == 200
    data = put_response.json()
    assert data["id"] == todo_id
    assert data["title"] == "Walk the cat"
    assert data["completed"] is True
    assert data["description"] == "New description"

    # Verify update
    get_response = client.get(f"/todos/{todo_id}")
    assert get_response.status_code == 200
    assert get_response.json()["title"] == "Walk the cat"
    assert get_response.json()["completed"] is True
    assert get_response.json()["description"] == "New description"

    # Partial update
    patch_response = client.put(
        f"/todos/{todo_id}",
        json={"title": "Walk the dog again"}
    )
    assert patch_response.status_code == 200
    data = patch_response.json()
    assert data["id"] == todo_id
    assert data["title"] == "Walk the dog again"
    assert data["completed"] is True
    assert data["description"] == "New description"

    # Test non-existent todo update
    not_found_response = client.put(
        "/todos/999",
        json={"title": "Non existent"}
    )
    assert not_found_response.status_code == 404
    assert not_found_response.json() == {"detail": "Todo not found"}


def test_delete_todo(client):
    # Create a todo
    post_response = client.post(
        "/todos",
        json={"title": "Clean room"}
    )
    todo_id = post_response.json()["id"]

    # Delete it
    delete_response = client.delete(f"/todos/{todo_id}")
    assert delete_response.status_code == 204

    # Verify it's gone
    get_response = client.get(f"/todos/{todo_id}")
    assert get_response.status_code == 404

    # Test non-existent todo delete
    not_found_response = client.delete("/todos/999")
    assert not_found_response.status_code == 404
    assert not_found_response.json() == {"detail": "Todo not found"}


def test_create_todo_validation_error(client):
    # Empty title
    response = client.post(
        "/todos",
        json={"title": "", "description": "Invalid todo"}
    )
    assert response.status_code == 422

    # Missing title
    response = client.post(
        "/todos",
        json={"description": "Missing title"}
    )
    assert response.status_code == 422


def test_update_todo_validation_error(client):
    # Create a todo
    post_response = client.post(
        "/todos",
        json={"title": "Original title"}
    )
    todo_id = post_response.json()["id"]

    # Update with empty title
    response = client.put(
        f"/todos/{todo_id}",
        json={"title": ""}
    )
    assert response.status_code == 422
