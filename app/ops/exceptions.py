from fastapi import HTTPException, status


def raise_unauthorized_exception(detail: str = "Invalid authentication credentials"):
    """Raises an HTTPException for unauthorized access. Detail: `Invalid authentication
    credentials`"""
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"})