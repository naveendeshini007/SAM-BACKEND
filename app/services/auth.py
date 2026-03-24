from datetime import datetime
import uuid
from typing import Optional, Dict
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.admins import Admins
from app.models.users import Users
from app.core.security import verify_password, hash_password, create_access_token, create_refresh_token
from app.core.log_event import log_auth_event

# FUTURE COGNITO/SES MIGRATION:
# - Replace local password storage and verification with Cognito admin_initiate_auth / admin_create_user
# - Send temporary passwords via SES instead of returning them in API responses
# - Swap JWT creation/verification to use Cognito JWKS and RS256
# - Use Cognito refresh handling instead of local token rotation


async def authenticate_and_login(db: AsyncSession, username_or_email: str, password: str) -> Dict:
    """Authenticate a principal (admin or user), log event, update last_login and return tokens/info.

    Returns dict with keys: access_token (str|None), refresh_token (str|None), id (str), is_admin (bool), require_password_change (bool)
    """
    try:
        # check admin first
        check = await db.execute(select(Admins).where((Admins.username == username_or_email) | (Admins.email == username_or_email)))
        admin = check.scalars().first()
        user = None
        if not admin:
            q2 = await db.execute(select(Users).where((Users.username == username_or_email) | (Users.email == username_or_email)))
            user = q2.scalars().first()

        target = admin or user
        if not target:
            # no principal found
            return {"error": "invalid_credentials"}

        if not verify_password(password, target.password_hash):
            # log failure
            await log_auth_event(db, "admin" if admin else "user", admin.admin_id if admin else user.user_id, "login_failure", False, note="invalid credentials")
            return {"error": "invalid_credentials"}

        # success
        await log_auth_event(db, "admin" if admin else "user", admin.admin_id if admin else user.user_id, "login_success", True)

        # update last_login_at
        if admin:
            stmt = update(Admins).where(Admins.admin_id == admin.admin_id).values(last_login_at=datetime.utcnow())
        else:
            stmt = update(Users).where(Users.user_id == user.user_id).values(last_login_at=datetime.utcnow())
        await db.execute(stmt)
        await db.commit()

        require_password_change = bool(target.must_change_password)
        principal_id = str(admin.admin_id if admin else user.user_id)
        is_admin = bool(admin is not None)

        if require_password_change:
            return {"require_password_change": True, "id": principal_id, "is_admin": is_admin}

        access_token = create_access_token(principal_id, "admin" if is_admin else "user", target.token_version)
        refresh_token = create_refresh_token(principal_id, "admin" if is_admin else "user", target.token_version)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "id": principal_id,
            "is_admin": is_admin,
            "require_password_change": False,
        }
    except Exception as exc:
        raise RuntimeError(f"authenticate_and_login failed: {exc}")


async def change_password_service(
    db: AsyncSession,
    principal,
    is_admin: bool,
    old_password: Optional[str],
    new_password: str,
    require_current_password: bool = False,
) -> Dict:
    """Change a principal's password.

    If `require_current_password` is True, the current password (old_password)
    will be validated even if `principal.must_change_password` is True. This is
    useful for unauthenticated first-login flows where the client proves identity
    by providing the temporary password.
    """
    try:
        if (not principal.must_change_password) or require_current_password:
            if not old_password or not verify_password(old_password, principal.password_hash):
                # determine id for logging
                pid = principal.admin_id if is_admin else principal.user_id
                await log_auth_event(db, "admin" if is_admin else "user", pid, "password_change", False, note="old password mismatch")
                return {"error": "old_password_mismatch"}

        new_hash = hash_password(new_password)
        if is_admin:
            stmt = update(Admins).where(Admins.admin_id == principal.admin_id).values(password_hash=new_hash, must_change_password=False)
        else:
            stmt = update(Users).where(Users.user_id == principal.user_id).values(password_hash=new_hash, must_change_password=False)

        await db.execute(stmt)
        await db.commit()
        pid = principal.admin_id if is_admin else principal.user_id
        await log_auth_event(db, "admin" if is_admin else "user", pid, "password_change", True)
        return {"ok": True}
    except Exception as exc:
        raise RuntimeError(f"change_password_service failed: {exc}")




async def rotate_refresh_and_issue(db: AsyncSession, user_type: str, user_id: str):
    try:
        # increment token_version and return new tokens
        if user_type == "admin":
            stmt = update(Admins).where(Admins.admin_id == uuid.UUID(user_id)).values(token_version=Admins.token_version + 1)
        else:
            stmt = update(Users).where(Users.user_id == uuid.UUID(user_id)).values(token_version=Users.token_version + 1)
        await db.execute(stmt)
        await db.commit()

        if user_type == "admin":
            admin = await db.execute(select(Admins).where(Admins.admin_id == uuid.UUID(user_id)))
            target = admin.scalars().first()
        else:
            user = await db.execute(select(Users).where(Users.user_id == uuid.UUID(user_id)))
            target = user.scalars().first()

        access_token = create_access_token(user_id, user_type, target.token_version)
        refresh_token = create_refresh_token(user_id, user_type, target.token_version)
        await log_auth_event(db, user_type, uuid.UUID(user_id), "login_success", True, note="refresh")
        return {"access_token": access_token, "refresh_token": refresh_token}
    except Exception as exc:
        raise RuntimeError(f"rotate_refresh_and_issue failed: {exc}")




async def refresh_service(db: AsyncSession, refresh_token: str):
    """Validate refresh token payload and rotate/issue new tokens.

    Returns dict with access_token and refresh_token on success.
    Raises RuntimeError on failure.
    """
    try:
        from app.core.security import decode_token

        payload = decode_token(refresh_token)
        if not payload or not payload.get("rt"):
            raise RuntimeError("invalid_refresh_token")

        user_type = payload.get("type")
        user_id = payload.get("sub")
        if not user_type or not user_id:
            raise RuntimeError("invalid_refresh_token_payload")

        tokens = await rotate_refresh_and_issue(db, user_type, user_id)
        return tokens
    except Exception as exc:
        raise RuntimeError(f"refresh_service failed: {exc}")


async def logout_service(db: AsyncSession, principal, is_admin: bool):
    """Perform logout actions: increment token_version and log an auth_event.

    Returns {'ok': True} on success or raises RuntimeError on failure.
    """
    try:
        if is_admin:
            stmt = update(Admins).where(Admins.admin_id == principal.admin_id).values(token_version=Admins.token_version + 1)
            await db.execute(stmt)
            await db.commit()
            await log_auth_event(db, "admin", principal.admin_id, "logout", True)
        else:
            stmt = update(Users).where(Users.user_id == principal.user_id).values(token_version=Users.token_version + 1)
            await db.execute(stmt)
            await db.commit()
            await log_auth_event(db, "user", principal.user_id, "logout", True)

        return {"ok": True}
    except Exception as exc:
        raise RuntimeError(f"logout_service failed: {exc}")
