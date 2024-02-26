import logging.config
from contextlib import asynccontextmanager
from fastapi import FastAPI

from db import engine, Base
from routes.auth import router as auth_router
from routes.root import router as root_router


logging.config.fileConfig("app/config/logging.conf", disable_existing_loggers=False)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting the application ...")
    logger.debug(f"Logging level: {logging.getLevelName(logger.getEffectiveLevel())}")
    Base.metadata.create_all(bind=engine)
    yield
    logger.info("Shutting down the application")


# RUN USING:   uvicorn app.main:app --reload --log-level debug
app = FastAPI(lifespan=lifespan)
app.include_router(root_router)
app.include_router(auth_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)