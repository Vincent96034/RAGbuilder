import logging
from typing import Optional

from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from fastapi.requests import Request
from fastapi import HTTPException, status, Security
from firebase_admin import auth

from app.db.models import UserModel
from app.schemas import CurrentUserSchema, TokenSchema
from app.ops.exceptions import raise_unauthorized_exception


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


async def get_token_from_request(request: Request) -> Optional[str]:
    """Attempt to extract the token from the Authorization header; if not found, check
    cookies."""
    token = request.cookies.get("access_token", None)
    if token is None:
        logger.debug("Token not found in cookies")
        token: str = await oauth2_bearer(request)
    return token


async def get_current_user(auth: HTTPAuthorizationCredentials = Security(security)):
    """Extracts and validates the user's token, either from the Authorization header or
    cookies, to retrieve the current user."""
    token = auth.credentials
    logger.debug(f"Token: {token}")
    return authenticate_user(token)


# async def get_current_user(request: Request) -> CurrentUserSchema:
#     """Extracts and validates the user's token, either from the Authorization header or
#     cookies, to retrieve the current user."""
#     token = await get_token_from_request(request)
#     if token is None:
#         raise_unauthorized_exception("Not authenticated")
#     if token.startswith("Bearer "):
#         token = token[7:]
#     return authenticate_user(token)


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
    

def create_access_token(email: str, password: str) -> TokenSchema:
    """Create an access token for a user.

    Args:
        email (str): The user's email.
        password (str): The user's password.

    Returns:
        dict: A dictionary containing the access token and token type.
    """
    user = auth.sign_in_with_email_and_password(
        email = email,
        password = password
    )
    return TokenSchema(token=user['idToken'])


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
