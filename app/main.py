from typing import Annotated
import logging.config

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import HTTPException

#from app.db.models import (User) # noqa: F401
from app.db import engine, Base
from app.schemas import CurrentUserSchema
from app.ops.user_ops import get_current_user
from app.routes.auth import router as auth_router


logging.config.fileConfig("app/config/logging.conf", disable_existing_loggers=False)
logger = logging.getLogger('app')

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting the application")
    logger.info("Creating DB")
    Base.metadata.create_all(bind=engine) # change this in production
    yield
    logger.info("Shutting down the application")


app = FastAPI(lifespan=lifespan) # run with: uvicorn app.main:app --reload


# include the routers
app.include_router(auth_router)


# mount the templates directory
templates = Jinja2Templates(directory="templates")


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(name="home.html", context={"request": request})


@app.get("/user")
async def user(user: Annotated[CurrentUserSchema, Depends(get_current_user)]) -> dict:
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"User": user}
