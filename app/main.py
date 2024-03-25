import logging.config
import os
import json

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.auth import router as auth_router
from app.routes.root import router as root_router
from app.routes.project import router as project_router
from app.routes.model import router as model_router
from app.routes.api import router as api_router

from app.utils.testing import create_test_token
from contextlib import asynccontextmanager


load_dotenv(".env")
logging.config.fileConfig("app/config/logging.conf", disable_existing_loggers=False)
logger = logging.getLogger(__name__)

if not firebase_admin._apps:

    fb_service_acc_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON_PATH")
    fb_service_acc_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

    if fb_service_acc_json:
        cred_dict = json.loads(fb_service_acc_json)
        cred = credentials.Certificate(cred_dict)
        logger.info("Firebase credentials loaded from json.")
    elif fb_service_acc_path:
        with open(fb_service_acc_path, 'r') as file:
            cred_dict = json.load(file)
            cred = credentials.Certificate(cred_dict)
        logger.info("Firebase credentials loaded from path.")
    else:
        cred = credentials.ApplicationDefault()
        logger.warning("No Firebase service account provided. Using App Default ...")

    default_app = firebase_admin.initialize_app(cred)
logger.info("Firebase app initialized: %s", default_app.name)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting the application ...")
    logger.debug(f"Logging level: {logging.getLevelName(logger.getEffectiveLevel())}")
    if os.getenv("SERVER_ENVIRONMENT") == "testing":
        test_token = create_test_token()
        logger.debug(f"Test token: {test_token}")
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
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")