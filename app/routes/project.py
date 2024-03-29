import logging
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, File, UploadFile, BackgroundTasks, Form
from fastapi.exceptions import HTTPException

from app.db.database import get_db
from app.file_handler import FileHandler
from app.ops.user_ops import get_current_user
from app.schemas import (
    CurrentUserSchema,
    CreateProjectSchema,
    UpdateProjectSchema,
    ProjectSchema,
    CreateFileSchema,
    FileSchema,
    DeleteFileSchema
)
from app.ops.project_ops import (
    update_project,
    get_projects_for_user,
    create_project,
    delete_project,
    check_user_project_access,
    process_and_upload_document,
    get_model_type,
    create_file,
    get_multiple_files,
    get_file,
    deindex_and_delete_files,
    check_file_metadatas
)


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
    """Get a single project by its ID.
    
    Args:
        project_id (str): The ID of the project to get.

    Returns:
        ProjectSchema: The project.
    """
    # check if the user is the owner of the project
    project = check_user_project_access(project_id, current_user.user_id, db)
    return ProjectSchema.from_model(project)


@router.patch("/{project_id}", response_model=ProjectSchema)
async def update_project_from_user(
    project: UpdateProjectSchema,
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
    db=Depends(get_db)
) -> ProjectSchema:
    """Update a single project by its ID.
    
    Args:
        project (UpdateProjectSchema): The updated project.

    Returns:
        ProjectSchema: The updated project.
    """
    check_user_project_access(project.project_id, current_user.user_id, db)
    return ProjectSchema.from_model(update_project(project, db))


@router.get("/", response_model=List[ProjectSchema])
async def read_projects_for_user(
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
    db=Depends(get_db)
) -> List[ProjectSchema]:
    """Get all projects for the current user.
    
    Args:
        None

    Returns:
        List[ProjectSchema]: A list of projects.
    """
    projects = get_projects_for_user(current_user.user_id, db)
    return [ProjectSchema.from_model(project) for project in projects]


@router.post("/", response_model=ProjectSchema)
async def create_project_for_user(
    project: CreateProjectSchema,
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
    db=Depends(get_db)
) -> ProjectSchema:
    """Create a new project.
    
    Args:
        project (CreateProjectSchema): The project to create.

    Returns:
        ProjectSchema: The created project.
    """
    project_obj = create_project(project, current_user.user_id, db)
    return ProjectSchema.from_model(project_obj)


@router.delete("/{project_id}", response_model=dict)
async def delete_project_for_user(
    project_id: str,
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
    db=Depends(get_db)
) -> dict:
    """Delete a project by its ID.
    
    Args:
        project_id (str): The ID of the project to delete.

    Returns:
        dict: A message indicating the project was deleted successfully.
    """
    check_user_project_access(project_id, current_user.user_id, db)
    return delete_project(project_id, current_user.user_id, db)


@router.post("/{project_id}/upload-files", response_model=dict)
async def create_upload_files(
    project_id: str,
    background_tasks: BackgroundTasks,
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
    files: List[UploadFile] = File(...),
    metadatas: Optional[str] = Form(...),
    db=Depends(get_db)
) -> dict:
    """Upload multiple files to a project. The files are processed in the background.
    
    Args:
        - project_id (str): The ID of the project to upload files to.
        - files (List[UploadFile]): The files to upload.
        - metadatas (Optional[str]): The metadata for the files. This is a JSON string and
            should be a dictionary with the file name as the key and the metadata as the
            value.

    Returns:
        dict: A message indicating the number of files uploaded and that they are now
            processing.
    
    ## Example metadata format:
        {
            "file1.txt": {"key1": "value1"},
            "file2.txt": {"key2": "value2"}
        }
    """
    project = check_user_project_access(project_id, current_user.user_id, db)
    metadatas = check_file_metadatas(metadatas)
    model = get_model_type(project.modeltype_id, db)

    for file in files:
        handler = FileHandler().get_handler(file)
        metadata = metadatas.get(file.filename, {})
        file_ref = CreateFileSchema(
            project_id=project_id,
            file_name=file.filename,
            file_type=handler.extension,
            metadata=metadata)
        file_model = create_file(file_ref, project_id, db)
        documents = await handler.read()
        background_task_kwargs = {
            "user_id": current_user.user_id,
            "file": file_model,
            "documents": documents,
            "project": project,
            "model": model,
            "db": db}
        background_tasks.add_task(process_and_upload_document, **background_task_kwargs)

    return {"message": f"{len(files)} files uploaded successfully: {files}. Now Processing..."}


@router.get("/{project_id}/files", response_model=list)
async def get_files_for_project(
    project_id: str,
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
    db=Depends(get_db)
) -> List[FileSchema]:
    """Get all files for a project.
    
    Args:
        project_id (str): The ID of the project to get files for.

    Returns:
        List: A list of files (FileSchema objects).
    """
    project = check_user_project_access(project_id, current_user.user_id, db)
    if project.files is None:
        return []
    files = get_multiple_files(project.files, db)
    return [FileSchema.from_model(file) for file in files]


@router.get("/{project_id}/files/{file_id}", response_model=list)
async def get_file_for_project(
    project_id: str,
    file_id: str,
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
    db=Depends(get_db)
) -> List:
    """Get a file from a project.
    
    Args: 
        - project_id (str): The ID of the project.
        - file_id (str): The ID of the file.

    Returns:
        FileSchema: The file.
    """
    project = check_user_project_access(project_id, current_user.user_id, db)
    if file_id not in project.files:
        raise HTTPException(status_code=404, detail="File not found in project")
    file = get_file(file_id, db)
    return FileSchema.from_model(file)


@router.delete("/{project_id}/files", response_model=dict)
async def delete_files_from_project(
    project_id: str,
    files: List[DeleteFileSchema],
    background_tasks: BackgroundTasks,
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
    db=Depends(get_db)
) -> dict:
    """Delete a file from a project. The file is deindexed according to the selected model
    and deleted in the background.
    
    Args:
        - project_id (str): The ID of the project.
        - files (List[DeleteFileSchema]): The files to delete.

    Returns:
        dict: A message indicating the file was deleted successfully.
    """
    project = check_user_project_access(project_id, current_user.user_id, db)
    model = get_model_type(project.modeltype_id, db)

    for file in files:
        if file.file_id not in project.files:
            raise HTTPException(status_code=404, detail=f"File {file.file_id} not found in project")
        
    for file in files:
        background_task_kwargs = {
            "file_id": file.file_id,
            "user_id": current_user.user_id,
            "project": project,
            "model": model,
            "db": db,}
        background_tasks.add_task(deindex_and_delete_files, **background_task_kwargs)

    return {"message": "File deleted successfully."}