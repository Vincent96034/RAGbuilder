import os
import logging
from typing import Optional
from dotenv import load_dotenv
from datetime import timedelta, datetime

from fastapi.security import OAuth2PasswordBearer
from fastapi.requests import Request
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.db.models import UserModel
from app.schemas import TokenSchema, CurrentUserSchema
from app.ops.exceptions import raise_unauthorized_exception


load_dotenv(".env")
logger = logging.getLogger('app')

# Get the values from the .env file
ENCRYPTION_SECRET_KEY = os.getenv("ENCRYPTION_SECRET_KEY")
ENCRYPTION_ALGORITHM = os.getenv("ENCRYPTION_ALGORITHM")

# Create the security context for the password
bcrypt = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/auth/token")


def authenticate_user(email: str, password: str, db: Session) -> UserModel:
    """Authenticate the user.

    Args:
        email (str): The user's email.
        password (str): The user's password.
        db (Session): The database session.

    Returns:
        User: The user object.
    """
    user = db.query(UserModel).filter(UserModel.email == email).first()
    if not user:
        return False
    if not bcrypt.verify(password, user.hashed_password):
        return False
    return user


def create_access_token(email: str, user_id: int, expires_delta: timedelta) -> TokenSchema:
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


async def get_token_from_request(request: Request) -> Optional[str]:
    """Attempt to extract the token from the Authorization header; if not found, check
    cookies."""
    token = request.cookies.get("access_token", None)
    if token is None:
        print("Calling from oauth2_bearer")
        token: str = await oauth2_bearer(request)
    return token


def decode_token(token: str) -> CurrentUserSchema:
    """Decodes the authentication token."""
    try:
        payload = jwt.decode(
            token=token,
            key=ENCRYPTION_SECRET_KEY,
            algorithms=[ENCRYPTION_ALGORITHM])
        email: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        if email is None or user_id is None:
            raise_unauthorized_exception()
        return CurrentUserSchema(email=email, user_id=user_id)
    except JWTError as err:
        logger.error(
            "JWT Error when decoding token. Invalid authentication credentials. "
            f"Error: {err}")
        raise_unauthorized_exception()


async def get_current_user(request: Request) -> CurrentUserSchema:
    """Extracts and validates the user's token, either from the Authorization header or
    cookies, to retrieve the current user."""
    token = await get_token_from_request(request)
    if token is None:
        raise_unauthorized_exception("Not authenticated")
    if token.startswith("Bearer "):
        token = token[7:]
    return decode_token(token)
    

def create_and_commit_user(email: str, password: str, db: Session) -> dict:
    """Create a new user in the database. Hashes the password before storing it.

    Args:
        request (dict): The request object containing user information.
        db (Session): The database session.

    Returns:
        None
    """
    create_user_model = UserModel(
        email=email,
        hashed_password=bcrypt.hash(password))
    db.add(create_user_model)
    db.commit()
    logger.debug(f"Created User '{email}'")
    return {"message": "User created successfully"}
    

def check_user_exists(email: str, db: Session) -> bool:
    """Check if a user exists in the database.

    Args:
        email (str): The user's email.
        db (Session): The database session.

    Returns:
        bool: True if the user exists, False otherwise.
    """
    return db.query(UserModel).filter(UserModel.email == email).first() is not None


def delete_and_commit_user(email: str, db: Session) -> dict:
    """Delete a user from the database.

    Args:
        email (str): The user's email.
        db (Session): The database session.

    Returns:
        None
    """
    db.query(UserModel).filter(UserModel.email == email).delete()
    db.commit()
    logger.debug(f"Deleted User '{email}'")
    return {"message": "User deleted successfully"}
