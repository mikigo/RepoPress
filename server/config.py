from __future__ import annotations
from pydantic_settings import BaseSettings


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


settings = Settings()
