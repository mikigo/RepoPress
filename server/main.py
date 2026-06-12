import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from tortoise import Tortoise

from config import settings

logger = logging.getLogger("repopress")

DATA_DIRS = [
    "data",
    "data/repos",
    "data/uploads",
]


def _ensure_data_dirs():
    """Create required data directories on startup."""
    for d in DATA_DIRS:
        os.makedirs(d, exist_ok=True)


async def _init_db():
    """Initialize Tortoise-ORM and create tables."""
    db_url = settings.database_url
    # Make SQLite path relative to project root
    if db_url.startswith("sqlite://") and not db_url[9:].startswith("/") and not db_url[9:].startswith("\\"):
        # Already a relative path, use as-is
        pass

    await Tortoise.init(
        db_url=db_url,
        modules={"models": ["models"]},
    )
    await Tortoise.generate_schemas()


async def _create_default_roles():
    """Ensure default roles (admin/editor/viewer) exist."""
    from models import Role

    for role_name in ("admin", "editor", "viewer"):
        exists = await Role.filter(name=role_name).first()
        if not exists:
            await Role.create(name=role_name, is_system=True)
            logger.info("Created default role: %s", role_name)


async def _create_default_superuser():
    """Create a default superuser if no users exist."""
    from models import User
    from services import create_user, get_password_hash
    from schemas import UserCreate

    user_count = await User.all().count()
    if user_count == 0:
        try:
            await create_user(
                UserCreate(
                    username="admin",
                    email="admin@repopress.local",
                    display_name="Administrator",
                    password="admin123",
                    is_superuser=True,
                )
            )
            logger.info("Created default superuser: admin / admin123")
        except Exception as exc:
            logger.warning("Could not create default superuser: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    # Startup
    _ensure_data_dirs()
    await _init_db()
    await _create_default_roles()
    await _create_default_superuser()
    logger.info("RepoPress server started")
    yield
    # Shutdown
    await Tortoise.close_connections()
    logger.info("RepoPress server shut down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="RepoPress API",
        description="Backend API for RepoPress documentation management",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Setup middleware
    from middleware import setup_middleware

    setup_middleware(app)

    # Register routers
    from routers.auth import router as auth_router
    from routers.admin import router as admin_router
    from routers.docs import router as docs_router

    app.include_router(auth_router)
    app.include_router(admin_router)
    app.include_router(docs_router)

    @app.get("/api/health")
    async def health_check():
        return {"status": "ok", "version": "0.1.0"}

    # Serve built frontend in production
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.isdir(static_dir):
        app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")
        # SPA fallback — serve index.html for all non-API routes
        @app.get("/{full_path:path}")
        async def spa_fallback(full_path: str):
            index_path = os.path.join(static_dir, "index.html")
            if os.path.isfile(index_path):
                return FileResponse(index_path)
            return {"detail": "Frontend not found"}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(
        level=logging.DEBUG if settings.debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
