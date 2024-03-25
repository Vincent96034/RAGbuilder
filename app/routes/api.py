import logging
from typing import Annotated, List

from dotenv import load_dotenv
from fastapi import Depends, APIRouter, HTTPException

from app.db.database import get_db
from app.schemas import CurrentUserSchema, InvokeResultSchema
from app.ops.user_ops import get_current_user
from app.ops.project_ops import check_user_project_access, get_project, get_model_type
from app.ops.model_factory import model_factory



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
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)],
    db=Depends(get_db)
) -> List[InvokeResultSchema]:
    """Invoke a model for a project."""
    # todo: implement API key authentication
    # todo: refactor into smaller functions (also see project_ops.py)
    # todo: better handle input data - allow for more complex data types
    # todo: better handle output data - remove some of the metadata

    if not check_user_project_access(project_id, current_user.user_id, db):
        logger.debug(f"User `{current_user.user_id}` does not have access to project `{project_id}`")
        raise HTTPException(
            status_code=403, detail="User does not have access to the project")
    project = get_project(project_id, db)
    model = get_model_type(project.modeltype_id, db)
    model_instance = model_factory(model.modeltype_id, model.config)
    logger.debug(
        f"Model instance `{model_instance}` loaded for project `{project.project_id}`")
    data = model_instance.invoke(
        input_data=input_data,
        filters = {},
        namespace = current_user.user_id,
        user_id = current_user.user_id,)
    logger.debug("Model invoked successfully")
    return data