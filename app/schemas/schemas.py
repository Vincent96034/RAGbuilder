from typing import TypeVar, Type, Optional
from pydantic import BaseModel


# Create a type variable for the model class
T = TypeVar('T')

class BaseSchema(BaseModel):
    """Base schema class that provides a method to create a schema from a model."""
    @classmethod
    def from_model(cls: Type[T], model: T) -> T:
        # Use Pydantic's model creation with **kwargs unpacking
        return cls(**model.__dict__)


class CreateUserRequestSchema(BaseSchema):
    first_name: str
    last_name: str
    email: str
    password: str


class TokenSchema(BaseSchema):
    token: str


class CurrentUserSchema(BaseSchema):
    email: str
    user_id: str


class CreateProjectSchema(BaseSchema):
    title: str
    description: str
    modeltype_id: str


class UpdateProjectSchema(BaseSchema):
    project_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    modeltype_id: Optional[str] = None


class ProjectSchema(BaseSchema):
    project_id: str
    title: str
    description: str
    modeltype_id: str
    created_at: str


class ModelTypeSchema(BaseSchema):
    modeltype_id: str
    title: str
    description: str
    config: dict


class CreateFileSchema(BaseSchema):
    project_id: str
    file_name: str
    file_type: str
    vec_db_src: Optional[str] = None
    vec_db_key: Optional[str] = None
    metadata: Optional[dict] = None

    
# remember to add new schemas to __all__ in app/schemas/__init__.py