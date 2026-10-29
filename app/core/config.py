from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "Proyecto Frontier API"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    data_dir: Path = Path(__file__).resolve().parents[2] / "data"
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
