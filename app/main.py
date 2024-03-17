import logging.config
import os
import json

from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.auth import router as auth_router
from app.routes.root import router as root_router
from contextlib import asynccontextmanager


load_dotenv(".env")
logging.config.fileConfig("app/config/logging.conf", disable_existing_loggers=False)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting the application ...")
    logger.debug(f"Logging level: {logging.getLevelName(logger.getEffectiveLevel())}")
    yield
    logger.info("Shutting down the application")


# RUN USING:   uvicorn app.main:app --reload
app = FastAPI(lifespan=lifespan)
app.include_router(root_router)
app.include_router(auth_router)


if not firebase_admin._apps:
    firebase_service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    if firebase_service_account_json:
        cred_dict = json.loads(firebase_service_account_json)
        cred = credentials.Certificate(cred_dict)
    else:
        cred = None
    default_app = firebase_admin.initialize_app(cred)


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