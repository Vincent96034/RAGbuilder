import logging
from dotenv import load_dotenv

from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from fastapi import HTTPException, status, Security
from firebase_admin import auth

from app.db.models import UserModel
from app.schemas import CurrentUserSchema
from app.ops.exceptions import raise_unauthorized_exception


load_dotenv(".env")
logger = logging.getLogger(__name__)
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/auth/token")
security = HTTPBearer()


def authenticate_user(token: str) -> CurrentUserSchema:
    """Authenticate the user from a token.

    Args:
        token (str): The user's token.

    Returns:
        User: The user object.
    """
    try:
        user = auth.verify_id_token(token, check_revoked=True)
        return CurrentUserSchema(email=user['email'], user_id=user['user_id'])
    except auth.RevokedIdTokenError:
        raise_unauthorized_exception("Revoked token.")
    except auth.ExpiredIdTokenError:
        raise_unauthorized_exception("Expired token.")
    except auth.InvalidIdTokenError:
        raise_unauthorized_exception("Invalid token.")


async def get_current_user(auth: HTTPAuthorizationCredentials = Security(security)):
    """Extracts and validates the user's token, either from the Authorization header or
    cookies, to retrieve the current user."""
    token = auth.credentials
    #logger.debug(f"Token: {token}")
    return authenticate_user(token)


def create_and_commit_user(first_name: str, last_name: str, email: str, password: str) -> UserModel:
    """Create a new user in the database. Hashes the password before storing it.

    Args:
        request (dict): The request object containing user information.
        db (Session): The database session.

    Returns:
        UserModel: The user object.
    """
    try:
        user = auth.create_user(
            email=email,
            email_verified=False,
            password=password,
            display_name=f'{first_name} {last_name}',
            disabled=False)
        logger.debug('Sucessfully created new user: {0}'.format(user.uid))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be a string with at least 6 characters.")
    return UserModel.from_firebase(user)


def check_user_exists(email: str) -> bool:
    """Check if a user exists in the database.

    Args:
        email (str): The user's email.

    Returns:
        bool: True if the user exists, False otherwise.
    """
    try:
        _ = auth.get_user_by_email(email)
        return True
    except auth.UserNotFoundError:
        return False
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid Email or Password format: {e}")


def delete_and_commit_user(email: str) -> dict:
    """Delete a user from the database.

    Args:
        email (str): The user's email.

    Returns:
        None
    """
    uid = auth.get_user_by_email(email).uid
    auth.delete_user(uid)
    logger.debug(f"Deleted User '{email}'")
    return {"message": "User deleted successfully"}

