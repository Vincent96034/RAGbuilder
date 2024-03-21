from firebase_admin import firestore
from google.cloud.firestore_v1 import FieldFilter

from fastapi.exceptions import HTTPException

from app.db.models import ProjectModel
from app.schemas import CreateProjectSchema, UpdateProjectSchema
from app.utils import logger


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
    updated_doc = project_ref.get() # fetch the data again
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
    doc_ref.set(data) # add data to collection
    created_doc = doc_ref.get() # fetch the data again
    if created_doc.exists:
        return ProjectModel.from_firebase(created_doc)
    else:
        raise Exception("Failed to create the project correctly.")


def delete_project(
        project_id: str, user_id: str, db: firestore.client) -> dict:
    db.collection("projects").document(project_id).delete()
    return {"message": "Project deleted successfully"}


def check_user_project_access(project_id: str, user_id: str, db: firestore.client) -> bool:
    doc_ref = db.collection("projects").document(project_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Project not found")
    project = ProjectModel.from_firebase(doc)
    return project.user_id == user_id
