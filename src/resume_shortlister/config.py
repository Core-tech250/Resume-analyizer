from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "Explainable Anonymized Resume Shortlisting System"
    VERSION: str = "0.1.0-phase1"
    DATABASE_URL: str = f"sqlite:///{PROJECT_ROOT / 'resumes.db'}"
    UPLOAD_DIR: Path = PROJECT_ROOT / "uploads"
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    USE_TFIDF_FALLBACK: bool = True
    OCR_ENABLED: bool = True
    TESSERACT_CMD: str = ""  # If on Windows, e.g. "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
