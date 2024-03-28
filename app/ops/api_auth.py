import os
import hashlib
import secrets
import logging
from dotenv import load_dotenv
from datetime import datetime, timedelta

from fastapi import HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.cloud import firestore

from app.db.database import get_db
from app.schemas import ApiUserSchema
from app.db.models import ApiKeyModel


logger = logging.getLogger(__name__)
load_dotenv(".env")
API_KEY_PREFIX = os.getenv("API_KEY_PREFIX") or "rb"
security = HTTPBearer()


async def get_api_user(
        auth: HTTPAuthorizationCredentials = Security(security),
        db: firestore.Client = Depends(get_db)
        ) -> ApiUserSchema:
    """Get the user associated with an API token. This is a dependency for FastAPI routes.

    Args:
        - auth (HTTPAuthorizationCredentials): The HTTP authorization credentials
        - db (firestore.Client): The Firestore client
    
    Returns:
        - ApiUserSchema: The API key schema for the user
    """
    token = auth.credentials
    return verify_api_token(token, db)


async def create_api_key(user_id: str, db: firestore.Client) -> ApiKeyModel:
    """Create an API key for a user. If the user already has an API key, return it.
    
    Args:
        - user_id (str): The user's ID
        - db (firestore.Client): The Firestore client

    Returns:
        - ApiKeyModel: The created or existing API key
    """
    existing_key = db.collection("api_keys").where("user_id", "==", user_id).get()
    if existing_key:
        logger.debug(f"User {user_id} already has an API key")
        return ApiKeyModel.from_firebase(existing_key[0])
    api_key = _generate_api_token()
    doc_ref = db.collection("api_keys").document(api_key)
    doc_ref.set({
        "user_id": user_id,
        "created_at": firestore.SERVER_TIMESTAMP,
        "expires_at": datetime.now()+ timedelta(weeks=52)
    })
    created_doc = doc_ref.get()  # fetch the data again
    if created_doc.exists:
        logger.debug(f"Created API key for user {user_id}")
        return ApiKeyModel.from_firebase(created_doc)
    else:
        raise Exception("Failed to create the api_key correctly.")
    

async def delete_api_key(api_key: str, user_id: str, db: firestore.Client) -> dict:
    """Delete an API key from the database."""
    doc_ref = db.collection("api_keys").document(api_key)
    api_token = doc_ref.get()
    if not api_token.exists:
        raise HTTPException(401, "Invalid API token")
    if api_token.get("user_id") != user_id:
        raise HTTPException(401, "Invalid API token")
    doc_ref.delete()
    return {"message": "API key deleted"}
    

def get_api_key_from_db(api_key: str, db: firestore.Client) -> ApiKeyModel:
    """Get an API key from the database."""
    doc_ref = db.collection("api_keys").document(api_key)
    api_token = doc_ref.get()
    if not api_token.exists:
        raise HTTPException(401, "Invalid API token")
    validate_api_key_expiry(api_token.get("expires_at"))
    return ApiKeyModel.from_firebase(api_token)


def verify_api_token(token: str, db: firestore.Client) -> ApiUserSchema:
    """Verify an API token. This checks the token's checksum and fetches the API key from
    the database. Returns the ApiUserSchema if the token is valid."""
    try:
        prefix, token_body, checksum = token.split('_')
        expected_checksum = hashlib.sha256(token_body.encode()).hexdigest()[:8]
        if not checksum == expected_checksum and prefix == API_KEY_PREFIX:
            raise HTTPException(401, "Invalid API token")
    except ValueError:
        raise HTTPException(401, "Invalid API token")
    api_key = get_api_key_from_db(token, db)
    return ApiUserSchema.from_model(api_key)


def validate_api_key_expiry(expires_at) -> None:
    """Validate the expiry of an API key."""
    if not expires_at:
        raise HTTPException(401, "Invalid API token data")
    if expires_at.tzinfo:
        # If 'expires_at' has timezone info, apply it to 'now'
        now = datetime.now(expires_at.tzinfo)
    else:
        # If 'expires_at' has no timezone info, consider it naive
        now = datetime.now()
    if now >= expires_at:
        raise HTTPException(401, "API token has expired")
    

def _generate_api_token() -> str:
    """Generate an API token. The token is a string with the format: 
    {prefix}_{token_body}_{checksum}"""
    prefix = API_KEY_PREFIX
    token_body = secrets.token_hex(16) 
    checksum = hashlib.sha256(token_body.encode()).hexdigest()[:8]
    return f"{prefix}_{token_body}_{checksum}"