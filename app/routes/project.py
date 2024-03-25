import logging
from typing import Annotated, List

from fastapi import APIRouter, Depends, File, UploadFile, BackgroundTasks
from fastapi.exceptions import HTTPException

from app.db.database import get_db
from app.file_handler import FileHandler
from app.ops.user_ops import get_current_user
from app.schemas import (CurrentUserSchema, CreateProjectSchema, UpdateProjectSchema, 
                         ProjectSchema, CreateFileSchema)
from app.ops.project_ops import (get_project, update_project, get_projects_for_user,
                                 create_project, delete_project, check_user_project_access,
                                 process_and_upload_document, get_model_type, create_file)


logger = logging.getLogger(__name__)

# Create the API router for the auth endpoints
router = APIRouter(
    prefix="/v1/projects",
    tags=["project"],
    responses={404: {"description": "Not found"}})


@router.get("/{project_id}", response_model=ProjectSchema)
async def read_project_from_user(
    project_id: str,
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
    db=Depends(get_db)
) -> ProjectSchema:
    """Get a single project by its ID."""
    # check if the user is the owner of the project
    if not check_user_project_access(project_id, current_user.user_id, db):
        raise HTTPException(
            status_code=403, detail="User does not have access to the project")
    return ProjectSchema.from_model(get_project(project_id, db))


@router.patch("/{project_id}", response_model=ProjectSchema)
async def update_project_from_user(
    project: UpdateProjectSchema,
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
    db=Depends(get_db)
) -> ProjectSchema:
    """Update a single project by its ID."""
    if not check_user_project_access(project.project_id, current_user.user_id, db):
        raise HTTPException(
            status_code=403, detail="User does not have access to the project")
    return ProjectSchema.from_model(update_project(project, db))


@router.get("/", response_model=List[ProjectSchema])
async def read_projects_for_user(
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
    db=Depends(get_db)
) -> List[ProjectSchema]:
    """Get all projects for the current user."""
    projects = get_projects_for_user(current_user.user_id, db)
    return [ProjectSchema.from_model(project) for project in projects]


@router.post("/", response_model=ProjectSchema)
async def create_project_for_user(
    project: CreateProjectSchema,
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
    db=Depends(get_db)
) -> ProjectSchema:
    """Create a new project."""
    return ProjectSchema.from_model(create_project(project, current_user.user_id, db))


@router.delete("/{project_id}", response_model=dict)
async def delete_project_for_user(
    project_id: str,
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
    db=Depends(get_db)
) -> dict:
    """Delete a project by its ID."""
    if not check_user_project_access(project_id, current_user.user_id, db):
        raise HTTPException(
            status_code=403, detail="User does not have access to the project")
    return delete_project(project_id, current_user.user_id, db)


@router.post("/{project_id}/upload-single-file", response_model=dict)
async def create_upload_file(
    project_id: str,
    background_tasks: BackgroundTasks,
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
    file: UploadFile = File(...),
    db=Depends(get_db)
) -> dict:
    """Upload a file to a project."""
    project = check_user_project_access(
        project_id, current_user.user_id, db, return_obj=True)
    if project is None:
        raise HTTPException(
            status_code=403, detail="User does not have access to the project")
    
    model = get_model_type(project.modeltype_id, db)
    handler = FileHandler().get_handler(file)
    file_ref = CreateFileSchema(
            project_id=project_id,
            file_name=file.filename,
            file_type=handler.extension,
            metadata={})
    file_model = create_file(file_ref, project_id, db)
    documents = await handler.read()

    logging_metadata = {'len': len(documents)}
    logger.debug(f"Loaded file successfully: \n {logging_metadata}")
    logger.debug(f"Metadata: \n {project} \n {model}")

    background_task_kwargs = {
        "user_id": current_user.user_id,
        "file": file_model,
        "documents": documents,
        "project": project,
        "model": model,
        "db": db}
    background_tasks.add_task(process_and_upload_document, **background_task_kwargs)
    return {"message": f"File {file.filename} uploaded successfully. Processing ..."}


@router.post("/{project_id}/upload-multiple-files", response_model=dict)
async def create_upload_files(
    project_id: str,
    background_tasks: BackgroundTasks,
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
    files: List[UploadFile] = File(...),
    db=Depends(get_db)
) -> dict:
    """Upload multiple files to a project."""
    project = check_user_project_access(
        project_id, current_user.user_id, db, return_obj=True)
    if project is None:
        raise HTTPException(
            status_code=403, detail="User does not have access to the project")
    model = get_model_type(project.modeltype_id, db)
    
    for file in files:  # Iterate over each file
        handler = FileHandler().get_handler(file)
        file_ref = CreateFileSchema(
            project_id=project_id,
            file_name=file.filename,
            file_type=handler.extension,
            metadata={})
        file_model = create_file(file_ref, project_id, db)
        documents = await handler.read()

        logging_metadata = {'len': len(documents), 'filename': file.filename}
        logger.debug(f"Loaded file successfully: {logging_metadata}")
        logger.debug(f"Metadata: \n {project} \n {model}")

        background_task_kwargs = {
            "user_id": current_user.user_id,
            "file": file_model,
            "documents": documents,
            "project": project,
            "model": model,
            "db": db}
        background_tasks.add_task(process_and_upload_document, **background_task_kwargs)
    
    return {"message": f"{len(files)} files uploaded successfully. Processing..."}
