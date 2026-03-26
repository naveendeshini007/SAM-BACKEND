from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ---------------- CORE ---------------- #
    ENV: str = "local"

    # ---------------- DATABASE ---------------- #
    DATABASE_URL: str | None = None

    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: str

    # ---------------- SECURITY ---------------- #
    SECRET_KEY: str = "localsecretkey"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REFRESH_COOKIE_SECURE: bool = False

    # ---------------- PIPELINE ---------------- #
    DOWNLOAD_FOLDER: str = "./data"
    LIMIT_ROWS: int = 10
    RETRIES: int = 3
    TIMEOUT: int = 60

    class Config:
        env_file = ".env"

    @model_validator(mode="after")
    def assemble_database_url(self) -> "Settings":
        """
        Keep async DB credentials consistent with the rest of the app.
        We prefer DB_* components to avoid mismatches between DATABASE_URL
        and DB_PASSWORD/DB_USER.
        """
        self.DATABASE_URL = (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
        return self


settings = Settings()


# ---------------- HELPER (for psycopg2) ---------------- #
def get_db_config():
    return {
        "dbname": settings.DB_NAME,
        "user": settings.DB_USER,
        "password": settings.DB_PASSWORD,
        "host": settings.DB_HOST,
        "port": settings.DB_PORT,
    }





















# from pydantic_settings import BaseSettings

# class Settings(BaseSettings):
#     DATABASE_URL: str
#     SECRET_KEY: str = "localsecretkey"
#     ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
#     REFRESH_TOKEN_EXPIRE_DAYS: int = 7

#     # For local testing only; set to True in prod
#     REFRESH_COOKIE_SECURE: bool = False

#     class Config:
#         env_file = ".env"


# settings = Settings()

# # my code
# import os
# from dotenv import load_dotenv

# load_dotenv()

# ENV = os.getenv("ENV", "local")

# DOWNLOAD_FOLDER = os.getenv("DOWNLOAD_FOLDER", "./data")

# DB_CONFIG = {
#     "dbname": os.getenv("DB_NAME"),
#     "user": os.getenv("DB_USER"),
#     "password": os.getenv("DB_PASSWORD"),
#     "host": os.getenv("DB_HOST"),
#     "port": os.getenv("DB_PORT"),
# }

# LIMIT_ROWS = 10000 if ENV == "local" else None
# RETRIES = 3
# TIMEOUT = 60