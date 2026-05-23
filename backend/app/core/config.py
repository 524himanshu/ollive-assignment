from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    GEMINI_API_KEY: str = ""
    POSTGRES_USER: str = "ollive"
    POSTGRES_PASSWORD: str = "ollive123"
    POSTGRES_DB: str = "ollive_db"
    POSTGRES_HOST: str = "127.0.0.1"
    POSTGRES_PORT: int = 5432
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    USE_SQLITE: bool = True  # Switch to False in Docker

    @property
    def DATABASE_URL(self) -> str:
        if self.USE_SQLITE:
            db_path = BASE_DIR / "ollive.db"
            return f"sqlite:///{db_path}"
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    class Config:
        env_file = str(BASE_DIR / ".env")
        extra = "ignore"


settings = Settings()