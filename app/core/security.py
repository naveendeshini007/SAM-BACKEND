from datetime import datetime, timedelta
from typing import Optional
import secrets
import string
import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    try:
        return pwd_context.hash(password)
    except Exception as exception:
        raise RuntimeError(f"hash_password failed: {exception}")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as exception:
        raise RuntimeError(f"verify_password failed: {exception}")


def _now_plus(minutes: int = 0, days: int = 0) -> datetime:
    try:
        return datetime.utcnow() + timedelta(minutes=minutes, days=days)
    except Exception as exception:
        raise RuntimeError(f"_now_plus failed: {exception}")


def create_access_token(subject: str, user_type: str, token_version: int) -> str:
    try:
        exp = _now_plus(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": subject,
            "type": user_type,
            "exp": exp,
            "token_version": token_version,
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    except Exception as exception:
        raise RuntimeError(f"create_access_token failed: {exception}")


def create_refresh_token(subject: str, user_type: str, token_version: int) -> str:
    try:
        exp = _now_plus(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        payload = {
            "sub": subject,
            "type": user_type,
            "exp": exp,
            "token_version": token_version,
            "rt": True,
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    except Exception as exception:
        raise RuntimeError(f"create_refresh_token failed: {exception}")


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.PyJWTError:
        return None


def generate_temp_password(length: int = 10) -> str:
    try:
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))
    except Exception as exception:
        raise RuntimeError(f"generate_temp_password failed: {exception}")

# FUTURE COGNITO MIGRATION:
# - Replace password_hash check with Cognito admin_initiate_auth / sign_in
# - For new user: Cognito admin_create_user + temporary_password + force password change
# - Email temp password via SES instead of returning in JSON
# - Replace JWT creation/verification with Cognito JWKS RS256
# - Refresh handled by Cognito SDK
