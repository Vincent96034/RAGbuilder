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
    logger.info("Starting the application ...")
    logger.info(f"Logging level: {logging.getLevelName(logger.getEffectiveLevel())}")
    Base.metadata.create_all(bind=engine)
    yield
    logger.info("Shutting down the application")


# RUN USING:   uvicorn app.main:app --reload
app = FastAPI(lifespan=lifespan)
app.include_router(root_router)
app.include_router(auth_router)
