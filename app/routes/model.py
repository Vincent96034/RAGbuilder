import logging
from typing import List, Annotated

from fastapi import APIRouter, Depends

from app.db.database import get_db
from app.ops.user_ops import get_current_user
from app.schemas import ModelTypeSchema, CurrentUserSchema
from app.ops.project_ops import get_model_types, get_model_type


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1/models",
    tags=["models"],
    responses={404: {"description": "Not found"}})


@router.get("/{modeltype_id}", response_model=ModelTypeSchema)
async def get_model_type_from_id(
    modeltype_id: str,
    _: Annotated[CurrentUserSchema, Depends(get_current_user)],
    db=Depends(get_db)
) -> ModelTypeSchema:
    """Get the model type from the modeltype_id.
    
    Args:
        modeltype_id (str): The ID of the model type.

    Returns:
        ModelTypeSchema: The model type.
    """
    return ModelTypeSchema.from_model(get_model_type(modeltype_id, db))


@router.get("/", response_model=List[ModelTypeSchema])
async def get_all_model_types(
    _: Annotated[CurrentUserSchema, Depends(get_current_user)],
    db=Depends(get_db)
) -> List[ModelTypeSchema]:
    """Get all model types.
    
    Args:
        None

    Returns:
        List[ModelTypeSchema]: A list of model types.
    """
    model_types = get_model_types(db)
    return [ModelTypeSchema.from_model(model_type) for model_type in model_types]