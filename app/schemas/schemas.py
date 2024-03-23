from typing import Optional
from pydantic import BaseModel


class CreateUserRequestSchema(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str


class TokenSchema(BaseModel):
    token: str


class CurrentUserSchema(BaseModel):
    email: str
    user_id: str


class CreateProjectSchema(BaseModel):
    title: str
    description: str
    instance_id: str


class UpdateProjectSchema(BaseModel):
    project_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    instance_id: Optional[str] = None

# remember to add new schemas to __all__ in app/schemas/__init__.py