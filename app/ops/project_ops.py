from fastapi import status
from firebase_admin import firestore

from app.db.models import ProjectModel
from app.schemas import CreateProjectSchema, UpdateProjectSchema
from app.utils import logger


def get_project(project_id: str, user_id: str, db: firestore.Client) -> ProjectModel:
    # todo
    return ""


def set_project(project: UpdateProjectSchema, db: firestore.Client) -> ProjectModel:
    logger.debug(f"Updating project {project.project_id}")
    project_ref = db.collection("projects").document(project.project_id)
    data = project.model_dump()
    data["updated_at"] = firestore.SERVER_TIMESTAMP
    return project_ref.update(data)


def get_projects_for_user(user_id: str, db: firestore.Client) -> list[ProjectModel]:
    # todo
    return ""


def create_project(
    project: CreateProjectSchema, user_id: str, db: firestore.Client) -> ProjectModel:
    logger.debug(f"Creating project {project.title}")
    data = project.model_dump()
    data["user_id"] = user_id
    data["created_at"] = firestore.SERVER_TIMESTAMP
    data["updated_at"] = firestore.SERVER_TIMESTAMP
    return db.collection("projects").add(data)


def delete_project(
        project_id: str, user_id: str, db: firestore.Client) -> status.HTTP_200_OK:
    db.collection("projects").document(project_id).delete()
    return status.HTTP_200_OK
