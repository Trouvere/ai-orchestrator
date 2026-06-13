from typing import Dict, List, Optional
from app.models import TodoInDB, TodoCreate, TodoUpdate

# In-memory database
todos_db: Dict[int, TodoInDB] = {}
next_id: int = 1

def get_all_todos() -> List[TodoInDB]:
    return list(todos_db.values())

def get_todo_by_id(todo_id: int) -> Optional[TodoInDB]:
    return todos_db.get(todo_id)

def create_todo(todo: TodoCreate) -> TodoInDB:
    global next_id
    new_todo = TodoInDB(id=next_id, **todo.model_dump())
    todos_db[next_id] = new_todo
    next_id += 1
    return new_todo

def update_todo(todo_id: int, todo_update: TodoUpdate) -> Optional[TodoInDB]:
    if todo_id not in todos_db:
        return None
    
    current_todo = todos_db[todo_id]
    update_data = todo_update.model_dump(exclude_unset=True)
    updated_todo_data = current_todo.model_dump()
    updated_todo_data.update(update_data)
    
    updated_todo = TodoInDB(**updated_todo_data)
    todos_db[todo_id] = updated_todo
    return updated_todo

def delete_todo(todo_id: int) -> Optional[TodoInDB]:
    return todos_db.pop(todo_id, None)

def reset_db():
    global todos_db, next_id
    todos_db = {}
    next_id = 1
