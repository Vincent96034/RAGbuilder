from typing import TypeVar, Type, Optional
from pydantic import BaseModel
from app.db.models import ProjectModel
from datetime import datetime


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


class FileSchema(BaseSchema):
    file_id: str
    file_name: str
    file_type: str
    metadata: Optional[dict] = None
    created_at: str

class InvokeResultSchema(BaseSchema):
    page_content: str
    metadata: dict


class DeleteFileSchema(BaseSchema):
    file_id: str


class FileMetadataSchema(BaseSchema):
    metadata: dict


# remember to add new schemas to __all__ in app/schemas/__init__.py
