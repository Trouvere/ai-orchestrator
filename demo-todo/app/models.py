from pydantic import BaseModel, Field
from typing import Optional

class TodoBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    completed: bool = False

class TodoCreate(TodoBase):
    pass

class TodoUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    completed: Optional[bool] = None

class TodoInDB(TodoBase):
    id: int

    class Config:
        from_attributes = True
