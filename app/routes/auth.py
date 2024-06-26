import logging
from typing import Annotated
from dotenv import load_dotenv

from fastapi import APIRouter, status, Depends
from fastapi.exceptions import HTTPException


from app.db.database import get_db
from app.schemas import (
    CreateUserRequestSchema,
    TokenSchema,
    CurrentUserSchema,
    ApiKeySchema
)
from app.ops.api_auth import create_api_key, delete_api_key
from app.ops.user_ops import (
    get_current_user,
    authenticate_user,
    create_and_commit_user,
    check_user_exists,
    delete_and_commit_user
)


load_dotenv(".env")
logger = logging.getLogger(__name__)

# Create the API router for the auth endpoints
router = APIRouter(
    prefix="/v1/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}})


@router.post("/user", status_code=status.HTTP_201_CREATED)
async def create_user(
    request: CreateUserRequestSchema
) -> dict:
    """Create a new user in the database.

    Args:
        request (CreateUserRequest): The request object containing user information.
        db (Session): The database session.

    Returns:
        dict: A message indicating the user was created.
    """
    logger.debug(f"Creating user with email: {request.email}")
    if check_user_exists(request.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists")
    user = create_and_commit_user(
        request.first_name, request.last_name, request.email, request.password)
    logger.debug(f"User created: {user.email}")
    return {"uid": user.user_id, "message": "User created successfully"}


@router.post("/token", response_model=CurrentUserSchema)
async def verify_token(
    token: TokenSchema,
) -> CurrentUserSchema:
    """Authenticates a user from token and returns the current user.

    Args:
        form_data (OAuth2PasswordRequestForm): The form data containing the user's email
            and password.
        db (Session): The database session.

    Returns:
        dict: A dictionary containing the access token and token type.
    """
    user = authenticate_user(token.token)
    logger.debug(f"User authenticated: {user.email}")
    return user


@router.delete("/user", status_code=status.HTTP_200_OK)
async def delete_user(
    user: Annotated[CurrentUserSchema, Depends(get_current_user)],
) -> dict:
    """Delete a user from the database.

    Args:
        request (CreateUserRequest): The request object containing user information.
        db (Session): The database session.
        current_user (User): The authenticated user.

    Returns:
        dict: A message indicating the user was deleted.
    """
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return delete_and_commit_user(user.email)


@router.post("/api_key", status_code=status.HTTP_201_CREATED)
async def create_api_key_for_user(
    user: Annotated[CurrentUserSchema, Depends(get_current_user)],
    db=Depends(get_db)
) -> ApiKeySchema:
    """Create an API key for a user.

    Args:
        user (User): The authenticated user.

    Returns:
        dict: A message indicating the API key was created.
    """
    api_key = create_api_key(user.user_id, db)
    logger.debug(f"API key created for user: {user.user_id}")
    return ApiKeySchema.from_model(api_key)
    

@router.delete("/api_key", status_code=status.HTTP_200_OK)
async def delete_api_key_for_user(
    api_key: str,
    user: Annotated[CurrentUserSchema, Depends(get_current_user)],
    db=Depends(get_db)
) -> dict:
    """Delete an API key for a user.

    Args:
        api_key (str): The API key to delete.
        user (User): The authenticated user.

    Returns:
        dict: A message indicating the API key was deleted.
    """
    logger.debug(f"Deleting API key for user: {user.user_id}")
    return delete_api_key(api_key, user.user_id, db)