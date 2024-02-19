import os
from dotenv import load_dotenv
from typing import Annotated
from datetime import timedelta, datetime

from fastapi import APIRouter, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.exceptions import HTTPException
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.db import get_db
from app.db.models import User
from app.schemas import CreateUserRequest, Token


# Load the .env file
load_dotenv(".env")

# Get the values from the .env file
ENCRYPTION_SECRET_KEY = os.getenv("ENCRYPTION_SECRET_KEY")
ENCRYPTION_ALGORITHM = os.getenv("ENCRYPTION_ALGORITHM")

# Create the API router for the auth endpoints
router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}})

# Create the security context for the password
bcrypt = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/auth/token")


def authenticate_user(email: str, password: str, db: Session) -> User:
    """Authenticate the user.

    Args:
        email (str): The user's email.
        password (str): The user's password.
        db (Session): The database session.

    Returns:
        User: The user object.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return False
    if not bcrypt.verify(password, user.hashed_password):
        return False
    return user


def create_access_token(email: str, user_id: int, expires_delta: timedelta) -> Token:
    """Create an access token for the user.

    Args:
        email (str): The user's email.
        user_id (int): The user's ID.
        expires_delta (timedelta): The expiration time for the token.

    Returns:
        Token: The token object.
    """
    to_encode = {"sub": email, "user_id": user_id}
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(
        claims=to_encode,
        key=ENCRYPTION_SECRET_KEY,
        algorithm=ENCRYPTION_ALGORITHM)

async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]) -> dict:
    """Retrieves the current user based on the provided token.

    Args:
        token (str): The authentication token.

    Returns:
        dict: A dictionary containing the email and user ID of the current user.
    """
    try:
        payload = jwt.decode(
            token=token,
            key=ENCRYPTION_SECRET_KEY,
            algorithms=[ENCRYPTION_ALGORITHM])
        email: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        if email is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"})
        return {"email": email, "user_id": user_id}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"})


@router.post("/create_user", status_code=status.HTTP_201_CREATED)
async def create_user(
    request: CreateUserRequest,
    db: Annotated[Session, Depends(get_db)]
) -> None:
    """Create a new user in the database.

    Args:
        request (CreateUserRequest): The request object containing user information.
        db (Session): The database session.

    Returns:
        None
    """
    create_user_model = User(
        email=request.email,
        hashed_password=bcrypt.hash(request.password))
    db.add(create_user_model)
    db.commit()


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)]) -> dict:
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
    token = create_access_token(user.email, user.id, timedelta(minutes=30))
    return {"access_token": token, "token_type": "bearer"}
