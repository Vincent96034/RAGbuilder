import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates

from app.schemas import CurrentUserSchema
from app.ops.user_ops import get_current_user

logger = logging.getLogger(__name__)

# Create the API router for the auth endpoints
router = APIRouter(
    tags=["root"],
    responses={404: {"description": "Not found"}})

# mount the templates directory
templates = Jinja2Templates(directory="templates")


@router.get("/")
def root(request: Request):
    return templates.TemplateResponse(name="hello.html", context={"request": request})


@router.get("/home")
def home(request: Request, current_user: Annotated[CurrentUserSchema, Depends(get_current_user)]):
    return templates.TemplateResponse(name="home.html", context={"request": request})


@router.get("/login")
def login(request: Request):
    return templates.TemplateResponse(name="login_v4.html", context={"request": request})


@router.get("/user")
async def user(user: Annotated[CurrentUserSchema, Depends(get_current_user)]) -> dict:
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"User": user}