from __future__ import annotations
import os
import secrets
from pathlib import Path

from pydantic_settings import BaseSettings

JWT_SECRET_FILE = Path("data/.jwt_secret")


def _resolve_jwt_secret() -> str:
    """Return the JWT secret from env, or auto-generate and persist one."""
    env_val = os.getenv("REPOPRESS_JWT_SECRET")
    if env_val:
        return env_val
    if JWT_SECRET_FILE.exists():
        return JWT_SECRET_FILE.read_text().strip()
    secret = secrets.token_hex(32)
    JWT_SECRET_FILE.parent.mkdir(parents=True, exist_ok=True)
    JWT_SECRET_FILE.write_text(secret)
    return secret


class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    database_url: str = "sqlite://data/repopress.db"
    auth_mode: str = "authenticated"  # "open" | "authenticated"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 hours
    git_clone_dir: str = "data/repos"
    upload_dir: str = "data/uploads"
    max_upload_size: int = 10 * 1024 * 1024

    model_config = {"env_prefix": "REPOPRESS_"}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.jwt_secret == "change-me-in-production":
            object.__setattr__(self, "jwt_secret", _resolve_jwt_secret())


settings = Settings()
