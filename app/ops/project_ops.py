import json
from typing import List

from firebase_admin import firestore
from google.cloud.firestore import ArrayUnion
from google.cloud.firestore_v1 import FieldFilter
from google.cloud.firestore_v1.field_path import FieldPath
from fastapi.exceptions import HTTPException
from langchain.schema.document import Document

from app.db.models import ProjectModel, ModelTypeModel, FileModel
from app.schemas import CreateProjectSchema, UpdateProjectSchema, CreateFileSchema
from app.utils import logger
from app.ops.model_factory import model_factory

# these keys are not allowed in metadata and output data will be cleaned of these keys
SYSTEM_METADATA_KEYS = ["project_id", "file_id", "user_id"]


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
        detail_message: str = "User does not have access to the project."
) -> ProjectModel:
    """Check if the user has access to the project. Returns the project if the user has
    access, otherwise raises an HTTPException.
    """
    doc_ref = db.collection("projects").document(project_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Project not found")
    project = ProjectModel.from_firebase(doc)
    check = project.user_id == user_id
    if not check:
        raise HTTPException(
            status_code=403, detail=detail_message)
    return project


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


def get_file(file_id: str, db: firestore.client) -> FileModel:
    """Get a file by its ID. Raises an HTTPException if the file is not found.

    Args:
        - file_id (str): The ID of the file.
        - db (firestore.client): The Firestore client.

    Returns:
        FileModel: The file.
    """
    doc_ref = db.collection("files").document(file_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="File not found")
    return FileModel.from_firebase(doc)


def get_multiple_files(file_ids: List[str], db: firestore.client) -> List[FileModel]:
    """Get multiple files by their IDs. Raises an HTTPException if any of the files are
    not found.

    Args:
        - file_ids (List[str]): The IDs of the files.
        - db (firestore.client): The Firestore client.

    Returns:
        List[FileModel]: The files.
    """
    if not file_ids:
        return []
    files, missing_ids = [], []
    batch_size = 10  # Firestore has a limit of 10 in 'in' operator

    for i in range(0, len(file_ids), batch_size):
        batch_ids = file_ids[i:i+batch_size]
        docs = db.collection("files").where(
            FieldPath.document_id(), "in", batch_ids).stream()

        found_ids = set()
        for doc in docs:
            files.append(FileModel.from_firebase(doc))
            found_ids.add(doc.id)

        # Check for missing documents in this batch
        missing_ids.extend([file_id for file_id in batch_ids if file_id not in found_ids])

    if missing_ids:
        raise HTTPException(
            status_code=404, detail=f"{len(missing_ids)} Files not found: {', '.join(missing_ids)}")
    return files


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
    model_instance.index(
        documents=documents,
        namespace=user_id,
        metadata={"project_id": project.project_id, "file_id": file.file_id, "file_title": file.file_name})
    # update ProjectModel entry: add file
    project_ref = db.collection('projects').document(project.project_id)
    project_ref.update({'files': ArrayUnion([file.file_id])})
    logger.debug(f"File `{file.file_id}` processed and uploaded successfully.")


def deindex_and_delete_files(
        user_id: str,
        file_id: FileModel,
        project: ProjectModel,
        model: ModelTypeModel,
        db: firestore.client
) -> None:
    logger.debug(f"Background task: Deindexing and deleting file `{file_id}` ...")
    # create model instance and deindex documents
    model_instance = model_factory(model.modeltype_id, model.config)
    logger.debug(
        f"Model instance `{model_instance}` created for project `{project.project_id}`")
    model_instance.deindex(filter={"file_id": file_id}, namespace=user_id)
    # update ProjectModel entry: remove file
    project_ref = db.collection('projects').document(project.project_id)
    project_ref.update({'files': firestore.ArrayRemove([file_id])})
    # delete file
    db.collection('files').document(file_id).delete()
    logger.debug(f"File `{file_id}` deindexed and deleted successfully.")


def check_file_metadatas(metadatas) -> dict:
    if metadatas:
        metadatas = json.loads(metadatas)
        # validate that metadata is of form: {file_id: {metadata}}
        for file_id in metadatas.keys():
            if not isinstance(metadatas[file_id], dict):
                raise HTTPException(
                    status_code=400, detail="Metadata must be a dictionary")
            for key in metadatas[file_id].keys():
                if key in SYSTEM_METADATA_KEYS:
                    # remove keys that are not allowed
                    del metadatas[file_id][key]
                    logger.warning(
                        f"Metadata key `{key}` is not allowed and has been removed.")
    else:
        metadatas = {}
    return metadatas


def clean_system_metadata(data):
    if not isinstance(data, Document):
        return data
    for doc in data:
        for key in SYSTEM_METADATA_KEYS:
            if key in doc.metadata.keys():
                del doc.metadata[key]
    return data
