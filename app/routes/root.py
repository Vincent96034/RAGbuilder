from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates

from app.schemas import CurrentUserSchema
from app.ops.user_ops import get_current_user


# Create the API router for the auth endpoints
router = APIRouter(
    tags=["root"],
    responses={404: {"description": "Not found"}})

# mount the templates directory
templates = Jinja2Templates(directory="templates")

@router.get("/")
def home(request: Request):
    return templates.TemplateResponse(name="home.html", context={"request": request})


@router.get("/user")
async def user(user: Annotated[CurrentUserSchema, Depends(get_current_user)]) -> dict:
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"User": user}