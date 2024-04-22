import logging
from typing import Annotated, List

from dotenv import load_dotenv
from fastapi import Depends, APIRouter, HTTPException

from app.db.database import get_db
from app.schemas import ApiUserSchema, InvokeResultSchema
from app.ops.api_auth import get_api_user
from app.ops.model_factory import model_factory
from app.ops.project_ops import (
    check_user_project_access,
    get_project,
    get_model_type,
    clean_system_metadata
)


load_dotenv(".env")
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1/api",
    tags=["api"],
    responses={404: {"description": "Not found"}})


@router.get("/{project_id}/invoke")
async def invoke_model(
    project_id: str,
    input_data: str,
    current_user: Annotated[ApiUserSchema, Depends(get_api_user)],
    db=Depends(get_db)
) -> List[InvokeResultSchema]:
    """Invoke a model for a project.

    Args:
        - project_id (str): The ID of the project.
        - input_data (str): The input data for the model.

    Returns:
        List[InvokeResultSchema]: The result of the model invocation.
    """
    # todo: better handle input data - allow for more complex data types

    if not check_user_project_access(project_id, current_user.user_id, db):
        logger.debug(
            f"User `{current_user.user_id}` does not have access to project `{project_id}`")
        raise HTTPException(
            status_code=403, detail="User does not have access to the project")
    project = get_project(project_id, db)
    model = get_model_type(project.modeltype_id, db)
    model_instance = model_factory(model.modeltype_id, model.config)
    logger.debug(
        f"Model instance `{model_instance}` loaded for project `{project.project_id}`")
    data = model_instance.invoke(
        input_data=input_data,
        filters={"project_id": project_id},
        namespace=current_user.user_id)
    logger.debug("Model invoked successfully")
    data = clean_system_metadata(data)
    return data
