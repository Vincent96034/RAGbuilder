import logging
from typing import Annotated, List

from fastapi import APIRouter, Depends
from fastapi import status

from app.ops.user_ops import get_current_user
from app.schemas import CurrentUserSchema, CreateProjectSchema
from app.db.models import ProjectModel
from app.db.database import get_db

from app.ops.project_ops import (
    get_project, update_project, get_projects_for_user, create_project, delete_project)


logger = logging.getLogger(__name__)

# Create the API router for the auth endpoints
router = APIRouter(
    tags=["project"],
    responses={404: {"description": "Not found"}})


@router.get("/projects/{project_id}", response_model=ProjectModel)
async def read_project_from_user(
    project_id: str,
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
    db=Depends(get_db)
) -> ProjectModel:
    """Get a single project by its ID."""
    # check if the user is the owner of the project
    # todo
    return get_project(project_id, db)


@router.set("/projects/{project_id}", response_model=ProjectModel)
async def update_project_from_user(
    project_id: str,
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
    db=Depends(get_db)
) -> ProjectModel:
    """Update a single project by its ID."""
    # check if the user is the owner of the project
    # todo
    return update_project(project_id, current_user.user_id, db)


@router.get("/projects", response_model=List[ProjectModel])
async def read_projects_for_user(
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
    db=Depends(get_db)
) -> List[ProjectModel]:
    """Get all projects for the current user."""
    return get_projects_for_user(current_user.user_id, db)


@router.post("/projects", response_model=ProjectModel)
async def create_project_for_user(
    project: CreateProjectSchema,
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
    db=Depends(get_db)
) -> ProjectModel:
    """Create a new project."""
    return create_project(project, current_user.user_id, db)


@router.delete("/projects/{project_id}", response_model=status.HTTP_200_OK)
async def delete_project_for_user(
    project_id: str,
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
    db=Depends(get_db)
) -> status.HTTP_200_OK:
    """Delete a project by its ID."""
    # check if the user is the owner of the project
    # todo
    return delete_project(project_id, current_user.user_id, db)
