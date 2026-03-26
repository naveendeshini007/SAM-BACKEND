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

    # ---------------- DATABASE POOL ---------------- #
    # Size of the connection pool kept alive between requests.
    DB_POOL_SIZE: int = 5
    # Extra connections allowed above pool_size under burst load.
    DB_MAX_OVERFLOW: int = 10
    # Recycle connections after this many seconds to avoid stale connections.
    DB_POOL_RECYCLE: int = 3600

    # ---------------- PIPELINE ---------------- #
    DOWNLOAD_FOLDER: str = "./data"
    LIMIT_ROWS: int | None = 10
    # Number of records per asyncpg COPY batch. Tune based on available RAM.
    COPY_BATCH_SIZE: int = 200_000
    # When True, skip writing an intermediate clean file; parse raw .dat and
    # stream directly into Postgres COPY in a single pass (fastest path).
    SINGLE_PASS_LOAD: bool = True
    # Fallback: trust that the clean file has exactly 142 columns per row.
    TRUST_CLEANED_PIPE_ROWS: bool = True
    # Run COUNT(*) after load (expensive on large tables; off by default).
    ENABLE_POST_LOAD_COUNT: bool = False
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
