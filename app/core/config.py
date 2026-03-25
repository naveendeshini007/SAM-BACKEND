from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str = "localsecretkey"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # For local testing only; set to True in prod
    REFRESH_COOKIE_SECURE: bool = False

    class Config:
        env_file = ".env"


settings = Settings()