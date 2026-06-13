from fastapi import FastAPI, HTTPException, status
from typing import List

from app.models import TodoCreate, TodoUpdate, TodoInDB
from app import db

app = FastAPI(
    title="Todo List API",
    description="A simple REST API for managing todo items.",
    version="1.0.0"
)

@app.get("/todos", response_model=List[TodoInDB], summary="Get all todo items")
async def get_todos():
    """
    Retrieve a list of all todo items.
    """
    return db.get_all_todos()

@app.post("/todos", response_model=TodoInDB, status_code=status.HTTP_201_CREATED, summary="Create a new todo item")
async def create_todo(todo: TodoCreate):
    """
    Create a new todo item with the provided title, description, and completion status.
    """
    return db.create_todo(todo)

@app.get("/todos/{todo_id}", response_model=TodoInDB, summary="Get a single todo item by ID")
async def get_todo(todo_id: int):
    """
    Retrieve a single todo item by its unique ID.
    Raises a 404 error if the todo item is not found.
    """
    todo = db.get_todo_by_id(todo_id)
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return todo

@app.put("/todos/{todo_id}", response_model=TodoInDB, summary="Update an existing todo item")
async def update_todo(todo_id: int, todo_update: TodoUpdate):
    """
    Update an existing todo item identified by its ID.
    Only provided fields will be updated.
    Raises a 404 error if the todo item is not found.
    """
    updated_todo = db.update_todo(todo_id, todo_update)
    if updated_todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return updated_todo

@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a todo item")
async def delete_todo(todo_id: int):
    """
    Delete a todo item by its unique ID.
    Raises a 404 error if the todo item is not found.
    """
    deleted_todo = db.delete_todo(todo_id)
    if deleted_todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return # No content for 204
