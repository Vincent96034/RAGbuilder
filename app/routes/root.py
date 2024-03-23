import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.requests import Request

from app.ops.user_ops import get_current_user
from app.schemas import CurrentUserSchema


logger = logging.getLogger(__name__)

# Create the API router for the auth endpoints
router = APIRouter(
    tags=["root"],
    responses={404: {"description": "Not found"}})


@router.get("/")
def root(
    request: Request
) -> dict:
    return {"message": "Hello World"}


@router.get("/health/auth")
def health_check_auth(
    request: Request,
    current_user: Annotated[CurrentUserSchema, Depends(get_current_user)]
) -> dict:
    return {"message": "Auth service is healthy"}


@router.get("/privacy_policy")
async def privacy_policy():
    privacy_policy = """PRIVACY POLICY \n
    Do not use this service. The developer is not responsible for any damages caused by the use of this service. \n"""
    return {"message": privacy_policy}
