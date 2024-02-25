from fastapi import HTTPException, status


def raise_unauthorized_exception(detail: str = "Invalid authentication credentials"):
    """Raises an HTTPException for unauthorized access."""
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"})