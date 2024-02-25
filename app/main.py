import logging.config
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.db import engine, Base
from app.routes.auth import router as auth_router
from app.routes.root import router as root_router


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
app.include_router(root_router)
app.include_router(auth_router)
