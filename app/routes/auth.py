import os
import logging
from typing import Annotated
from datetime import timedelta
from dotenv import load_dotenv

from fastapi import APIRouter, status, Depends
from fastapi.responses import Response
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import CreateUserRequestSchema, TokenSchema, CurrentUserSchema

from app.ops.user_ops import (get_current_user, authenticate_user, create_token,
                              create_and_commit_user, check_user_exists, delete_and_commit_user)

load_dotenv(".env")
logger = logging.getLogger(__name__)

# Create the API router for the auth endpoints
router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}})

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES") or 30)
#VERIFICATION_TOKEN_EXPIRE_MINUTES = int(os.getenv("VERIFICATION_TOKEN_EXPIRE_MINUTES") or 7)


@router.post("/create_user", status_code=status.HTTP_201_CREATED)
async def create_user(
    request: CreateUserRequestSchema,
    db: Annotated[Session, Depends(get_db)]
) -> dict:
    """Create a new user in the database.

    Args:
        request (CreateUserRequest): The request object containing user information.
        db (Session): The database session.

    Returns:
        dict: A message indicating the user was created.
    """
    logger.debug(f"Creating user with email: {request.email}")
    if check_user_exists(request.email, db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists")
    _ = create_and_commit_user(request.first_name, request.last_name, request.email, request.password, db)
    return {"message": "User created successfully"}


@router.post("/token", response_model=TokenSchema)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)]
) -> dict:
    """Authenticates a user and generates an access token.

    Args:
        form_data (OAuth2PasswordRequestForm): The form data containing the user's email
            and password.
        db (Session): The database session.

    Returns:
        dict: A dictionary containing the access token and token type.
    """
    user = authenticate_user(
        email=form_data.username,
        password=form_data.password,
        db=db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"})
    token = create_token(
        user.email,
        user.id,
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": token, "token_type": "bearer"}


@router.post("/cookie_token")
async def cookie_login_for_access_token(
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    form_data: OAuth2PasswordRequestForm = Depends()
) -> dict:
    logger.debug(f"User with email '{form_data.username}' calling /cookie_token")
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"})
    token = create_token(
        user.email,
        user.id,
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        secure=True,
        samesite='Lax')
    return {"message": "Login successful"}


@router.post("/cookie_logout")
def cookie_logout(response: Response):
    response.delete_cookie("access_token")
    logger.debug("Logging out user")
    return {"message": "Logout successful"}


@router.delete("/delete_user", status_code=status.HTTP_200_OK)
async def delete_user(
    user: Annotated[CurrentUserSchema, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
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
    return delete_and_commit_user(user.email, db)


# @router.post("/register", status_code=status.HTTP_201_CREATED)
# async def register_user(
#     request: CreateUserRequestSchema,
#     db: Annotated[Session, Depends(get_db)]
# ) -> dict:
#     # create user in db
#     logger.debug(f"Creating user with email: {request.email}")
#     if check_user_exists(request.email, db):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="User already exists")
#     new_user = create_and_commit_user(
#         request.first_name, request.last_name, request.email, request.password, db)
#     # create verification token
#     verification_token = create_token(
#         new_user.email, new_user.user_id, expires_delta = VERIFICATION_TOKEN_EXPIRE_MINUTES)
#     create_and_commit_user_verification_token(new_user.email, verification_token, db)
#     # send email with verification token
#     send_user_verification_email(request.email, verification_token)
#     return {"message": "User created successfully"}


# @router.post("/verify_user/{verification_token}", status_code=status.HTTP_200_OK)
# async def verify_user(verification_token):
#     current_user = decode_token(verification_token)
#     if current_user is None:
#         raise HTTPException(status_code=401, detail="Unauthorized")
#     # verify user
#     verify_user_in_db(current_user.email)
#     delete_and_commit_user_verification_token(current_user.email)
#     return {"message": "User verified successfully"}