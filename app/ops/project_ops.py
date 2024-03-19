from fastapi import status
from firebase_admin import firestore

from app.db.models import ProjectModel
from app.schemas import CreateProjectSchema, UpdateProjectSchema
from app.utils import logger


def get_project(project_id: str, db: firestore.client) -> ProjectModel:
    doc_ref = db.collection("projects").document(project_id)
    doc = doc_ref.get()
    if doc.exists:
        data = doc.to_dict()
    else:
        print("No such document!")
    print(data)
    return ProjectModel.from_firebase(data)


def set_project(project: UpdateProjectSchema, db: firestore.client) -> ProjectModel:
    logger.debug(f"Updating project {project.project_id}")
    project_ref = db.collection("projects").document(project.project_id)
    data = project.model_dump()
    data["updated_at"] = firestore.SERVER_TIMESTAMP
    return project_ref.update(data)


def get_projects_for_user(user_id: str, db: firestore.client) -> list[ProjectModel]:
    # todo
    return ""


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
        project_id: str, user_id: str, db: firestore.client) -> status.HTTP_200_OK:
    db.collection("projects").document(project_id).delete()
    return status.HTTP_200_OK
