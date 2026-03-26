from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ---------------- CORE ---------------- #
    ENV: str = "local"

    # ---------------- DATABASE ---------------- #
    DATABASE_URL: str

    # ---------------- SECURITY ---------------- #
    SECRET_KEY: str = "localsecretkey"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REFRESH_COOKIE_SECURE: bool = False  # For local testing only; set to True in production

    # ---------------- PIPELINE ---------------- #
    DOWNLOAD_FOLDER: str = "./data"
    LIMIT_ROWS: int | None = 10
    RETRIES: int = 3
    TIMEOUT: int = 60

    class Config:
        env_file = ".env"

    @field_validator("LIMIT_ROWS", mode="before")
    @classmethod
    def normalize_limit_rows(cls, value):
        # Empty value in .env means no limit (load all rows).
        if value is None:
            return None
        if isinstance(value, str) and value.strip() == "":
            return None
        int_value = int(value)
        return int_value if int_value > 0 else None


settings = Settings()