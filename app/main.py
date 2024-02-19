from typing import Annotated

from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session

from app.db.models import (User) # noqa: F401
from app.db import engine, Base, get_db
from app.core.auth import router as auth_router, get_current_user
from utils.logging_config import logger



logger.setLevel("DEBUG")

# Create the FastAPI app
app = FastAPI() # run with: uvicorn app.main:app --reload
app.include_router(auth_router)

templates = Jinja2Templates(directory="templates")

# Create the database tables
Base.metadata.create_all(bind=engine)

# Dependency injection
db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/user")
async def user(user: user_dependency, db: db_dependency) -> dict:
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"User": user}
