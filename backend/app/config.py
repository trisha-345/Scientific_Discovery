from pydantic_settings import BaseSettings
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# In Docker/Render, use /app/data; locally use backend/data
_default_db_dir = Path("/app/data") if Path("/app").exists() else BASE_DIR / "data"
_default_db_dir.mkdir(parents=True, exist_ok=True)

DEFAULT_DB = f"sqlite:///{_default_db_dir}/app.db"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB)

DEFAULT_UPLOAD = (
    "/app/uploads" if Path("/app").exists() else str(BASE_DIR / "uploads")
)
Path(DEFAULT_UPLOAD).mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    APP_NAME: str = "Scientific Discovery Platform"
    DATABASE_URL: str = DATABASE_URL
    UPLOAD_DIR: str = DEFAULT_UPLOAD
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"

    class Config:
        env_file = str(BASE_DIR / ".env")


settings = Settings()