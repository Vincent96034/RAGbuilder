from typing import TypeVar, Type, Optional
from pydantic import BaseModel
from datetime import datetime

from app.db.models import ProjectModel


# Create a type variable for the model class
T = TypeVar('T')


class BaseSchema(BaseModel):
    """Base schema class that provides a method to create a schema from a model."""
    @classmethod
    def from_model(cls: Type[T], model: T) -> T:
        model_dict = model.__dict__.copy()
        for key, value in model_dict.items():
            # Check if the value is an instance of datetime and convert to string
            if isinstance(value, datetime):
                model_dict[key] = value.strftime('%Y-%m-%d %H:%M:%S')
        return cls(**model_dict)


class CreateUserRequestSchema(BaseSchema):
    """Schema for creating a new user."""
    first_name: str
    last_name: str
    email: str
    password: str


class TokenSchema(BaseSchema):
    """Schema for a token."""
    token: str


class CurrentUserSchema(BaseSchema):
    """Schema for the current user."""
    email: str
    user_id: str


class CreateProjectSchema(BaseSchema):
    """Schema for creating a new project."""
    title: str
    description: str
    modeltype_id: str


class UpdateProjectSchema(BaseSchema):
    """Schema for updating a project."""
    project_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    modeltype_id: Optional[str] = None


class ProjectSchema(BaseSchema):
    """Schema for a project."""
    project_id: str
    title: str
    description: str
    modeltype_id: str
    created_at: str

    @staticmethod
    def from_model(project: ProjectModel):
        datetime_str = project.created_at.strftime('%Y-%m-%d %H:%M:%S')
        return ProjectSchema(
            project_id=project.project_id,
            title=project.title,
            description=project.description,
            modeltype_id=project.modeltype_id,
            created_at=datetime_str)


class ModelTypeSchema(BaseSchema):
    """Schema for a model type."""
    modeltype_id: str
    title: str
    description: str
    config: dict


class CreateFileSchema(BaseSchema):
    """Schema for creating a new file."""
    project_id: str
    file_name: str
    file_type: str
    vec_db_src: Optional[str] = None
    vec_db_key: Optional[str] = None
    metadata: Optional[dict] = None


class FileSchema(BaseSchema):
    """Schema for a file."""
    file_id: str
    file_name: str
    file_type: str
    created_at: str
    metadata: Optional[dict] = None


class InvokeResultSchema(BaseSchema):
    """Schema for the result of invoking a model."""
    page_content: str
    metadata: dict


class DeleteFileSchema(BaseSchema):
    """Schema for deleting a file."""
    file_id: str


class FileMetadataSchema(BaseSchema):
    """Schema for file metadata."""
    metadata: dict


class ApiUserSchema(BaseSchema):
    """Schema for an API user (excluding the API key)."""
    user_id: str
    created_at: str
    expires_at: str


class ApiKeySchema(BaseSchema):
    """Schema for an API key."""
    api_key: str
    user_id: str
    created_at: str
    expires_at: str


class CreateStatusSchema(BaseSchema):
    status: str
    status_type: Optional[str] = None
    item_id: Optional[str] = None


class UpdateStatusSchema(BaseSchema):
    status: str


# remember to add new schemas to __all__ in app/schemas/__init__.py
