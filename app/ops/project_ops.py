from typing import List
from firebase_admin import firestore
from google.cloud.firestore import ArrayUnion
from google.cloud.firestore_v1 import FieldFilter
from fastapi.exceptions import HTTPException
from langchain.schema.document import Document

from app.db.models import ProjectModel, ModelTypeModel, FileModel
from app.schemas import CreateProjectSchema, UpdateProjectSchema, CreateFileSchema
from app.utils import logger
from app.ops.model_factory import model_factory


def get_project(project_id: str, db: firestore.client) -> ProjectModel:
    doc_ref = db.collection("projects").document(project_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectModel.from_firebase(doc)


def update_project(project: UpdateProjectSchema, db: firestore.client) -> ProjectModel:
    logger.debug(f"Updating project {project.project_id}")
    project_ref = db.collection("projects").document(project.project_id)
    data = project.model_dump()
    # remove keys with none values
    data = {k: v for k, v in data.items() if v is not None}
    data["updated_at"] = firestore.SERVER_TIMESTAMP
    project_ref.update(data)
    updated_doc = project_ref.get()  # fetch the data again
    if updated_doc.exists:
        return ProjectModel.from_firebase(updated_doc)
    else:
        raise Exception("Failed to update the project correctly.")


def get_projects_for_user(user_id: str, db: firestore.client) -> list[ProjectModel]:
    projects = (
        db.collection("projects")
        .where(filter=FieldFilter("user_id", "==", user_id))
        .stream())
    return [ProjectModel.from_firebase(project) for project in projects]


def create_project(
    project: CreateProjectSchema,
    user_id: str,
    db: firestore.client
) -> ProjectModel:
    """Create a new project in the database.

    Args:
        - project (CreateProjectSchema): The project to create.
        - user_id (str): The user ID of the user creating the project.
        - db (firestore.client): The Firestore client.

    Returns:
        ProjectModel: The created project.
    """
    logger.debug(f"Creating project {project.title}")
    data = project.model_dump()
    data["user_id"] = user_id
    data["created_at"] = firestore.SERVER_TIMESTAMP
    data["updated_at"] = firestore.SERVER_TIMESTAMP
    doc_ref = db.collection("projects").document()
    doc_ref.set(data)  # add data to collection
    created_doc = doc_ref.get()  # fetch the data again
    if created_doc.exists:
        return ProjectModel.from_firebase(created_doc)
    else:
        raise Exception("Failed to create the project correctly.")


def delete_project(
        project_id: str, user_id: str, db: firestore.client) -> dict:
    db.collection("projects").document(project_id).delete()
    return {"message": "Project deleted successfully"}


def check_user_project_access(
        project_id: str,
        user_id: str,
        db: firestore.client,
        return_obj=False
) -> bool | ProjectModel | None:
    """Check if the user has access to the project. If return_obj is True, returns the
    project object if user has access to it.
    """
    # todo: refactor
    doc_ref = db.collection("projects").document(project_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Project not found")
    project = ProjectModel.from_firebase(doc)
    check = project.user_id == user_id
    if return_obj:
        return project if check else None
    return check


def get_model_types(db: firestore.client) -> list[ModelTypeModel]:
    model_types = db.collection("models").stream()
    return [ModelTypeModel.from_firebase(model_type) for model_type in model_types]


def get_model_type(model_type_id: str, db: firestore.client) -> ModelTypeModel:
    doc_ref = db.collection("models").document(model_type_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Model type not found")
    return ModelTypeModel.from_firebase(doc)


def create_file(
    file: CreateFileSchema,
    project_id: str,
    db: firestore.client
) -> FileModel:
    """Create a new file in the database.

    Args:
        - file (CreateFileSchema): The file to create.
        - project_id (str): The project ID of the project the file belongs to.
        - db (firestore.client): The Firestore client.

    Returns:
        FileModel: The created file.
    """
    logger.debug(f"Creating file {file.file_name}")
    data = file.model_dump()
    data["project_id"] = project_id
    data["created_at"] = firestore.SERVER_TIMESTAMP
    doc_ref = db.collection("files").document()
    doc_ref.set(data)
    created_doc = doc_ref.get()
    if created_doc.exists:
        return FileModel.from_firebase(created_doc)
    else:
        raise Exception("Failed to create the file correctly.")


def process_and_upload_document(
        user_id: str,
        file: FileModel,
        documents: List[Document],
        project: ProjectModel,
        model: ModelTypeModel,
        db: firestore.client
) -> None:
    logger.debug(f"Background task: Processing and uploading file `{file.file_id}` ...")
    # create model instance and index documents
    model_instance = model_factory(model.modeltype_id, model.config)
    logger.debug(
        f"Model instance `{model_instance}` created for project `{project.project_id}`")
    logger.debug(f"Documents: {documents}")
    model_instance.index(
        documents=documents,
        namespace=user_id,
        metadata={"project_id": project.project_id, "file_id": file.file_id})
    # update ProjectModel entry: add file
    project_ref = db.collection('projects').document(project.project_id)
    project_ref.update({'files': ArrayUnion([file.file_id])})
    logger.debug(f"File `{file.file_id}` processed and uploaded successfully.")
