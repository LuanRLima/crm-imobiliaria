import os
from dataclasses import dataclass, field
from functools import lru_cache


def _build_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    host = os.getenv("POSTGRES_HOST")
    database = os.getenv("POSTGRES_DB")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    port = os.getenv("POSTGRES_PORT", "5432")

    if host and database and user and password:
        return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database}"

    return "sqlite:///./crm.db"


@dataclass(frozen=True)
class Settings:
    app_name: str = "CRM Imobiliária API"
    api_prefix: str = "/api/v1"
    database_url: str = _build_database_url()
    cors_origins: list[str] = field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )
    seed_admin_email: str = os.getenv(
        "SEED_ADMIN_EMAIL", "admin@crmimobiliaria.local"
    )
    seed_admin_password: str = os.getenv("SEED_ADMIN_PASSWORD", "Admin123!")


@lru_cache
def get_settings() -> Settings:
    return Settings()
