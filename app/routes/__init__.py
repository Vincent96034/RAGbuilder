from app.routes.auth import router as auth_router
from app.routes.root import router as root_router
from app.routes.project import router as project_router
from app.routes.model import router as model_router
from app.routes.api import router as api_router


__all__ = [
    "auth_router",
    "root_router",
    "project_router",
    "model_router",
    "api_router"
]