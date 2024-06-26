import os
import logging.config

import firebase_admin
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.utils.helpers import create_test_token, get_fb_cred
from app.routes import (
    root_router,
    auth_router,
    project_router,
    model_router,
    api_router
)


load_dotenv(".env")
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.config.fileConfig("app/config/logging.conf", disable_existing_loggers=False)
logger = logging.getLogger(__name__)
logger.setLevel(log_level)


if not firebase_admin._apps:
    cred = get_fb_cred()
    default_app = firebase_admin.initialize_app(cred)
logger.info("Firebase app initialized: %s", default_app.name)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting the application ...")
    logger.debug(f"Logging level: {logging.getLevelName(logger.getEffectiveLevel())}")
    if os.getenv("SERVER_ENVIRONMENT") == "testing":
        test_token = create_test_token()
        logger.debug(f"Test token:\n\n\n{test_token}\n\n")
    yield
    logger.info("Shutting down the application")


# RUN USING:   uvicorn app.main:app --reload
app = FastAPI(lifespan=lifespan)
app.include_router(root_router)
app.include_router(auth_router)
app.include_router(project_router)
app.include_router(model_router)
app.include_router(api_router)


origins = [
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level=log_level.lower())
