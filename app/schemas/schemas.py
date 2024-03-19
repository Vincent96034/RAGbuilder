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
    rag_type_id: str


class UpdateProjectSchema(BaseModel):
    project_id: str
    title: str
    description: str
    rag_type_id: str

# remember to add new schemas to __all__ in app/schemas/__init__.py