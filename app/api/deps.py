from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.core.security import decode_token
from app.models.admins import Admins
from app.models.users import Users
from typing import AsyncGenerator

async def get_db() -> AsyncGenerator[AsyncSession, None]:
	async with AsyncSessionLocal() as session:
		yield session


security = HTTPBearer(auto_error=False)


async def get_current_user(
	credentials: HTTPAuthorizationCredentials = Depends(security),
	db: AsyncSession = Depends(get_db),
):
    try:
        if not credentials:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        token = credentials.credentials
        payload = decode_token(token)
        if not payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
        if payload.get("type") != "user":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a user token")
        user_id = payload.get("sub")
        token_version = payload.get("token_version")
        users = await db.execute(select(Users).where(Users.user_id == user_id))
        user = users.scalars().first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if user.token_version != token_version:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")
        return user
    except Exception as exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exception))


async def get_current_admin(
	credentials: HTTPAuthorizationCredentials = Depends(security),
	db: AsyncSession = Depends(get_db),
):
    try:
        if not credentials:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        token = credentials.credentials
        payload = decode_token(token)
        if not payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
        if payload.get("type") != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not an admin token")
        admin_id = payload.get("sub")
        token_version = payload.get("token_version")
        admins = await db.execute(select(Admins).where(Admins.admin_id == admin_id))
        admin = admins.scalars().first()
        if not admin:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found")
        if admin.token_version != token_version:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")
        return admin
    except Exception as exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exception))


async def get_current_principal(
	credentials: HTTPAuthorizationCredentials = Depends(security),
	db: AsyncSession = Depends(get_db),
):  
    try:
        """Return either admin or user along with is_admin flag."""
        if not credentials:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        token = credentials.credentials
        payload = decode_token(token)
        if not payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
        user_type = payload.get("type")
        principal_id = payload.get("sub")
        token_version = payload.get("token_version")
        if user_type == "admin":
            principals = await db.execute(select(Admins).where(Admins.admin_id == principal_id))
            principal = principals.scalars().first()
            if not principal:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found")
            if principal.token_version != token_version:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")
            return principal, True
        else:
            principals = await db.execute(select(Users).where(Users.user_id == principal_id))
            principal = principals.scalars().first()
            if not principal:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            if principal.token_version != token_version:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")
            return principal, False
    except HTTPException as exception:
        raise exception
    except Exception as exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exception))


async def get_optional_current_principal(
	credentials: HTTPAuthorizationCredentials = Depends(security),
	db: AsyncSession = Depends(get_db),
):
    try:
        """Return (principal, is_admin) or (None, False) if no credentials provided."""
        if not credentials:
            return None, False
        token = credentials.credentials
        payload = decode_token(token)
        if not payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
        user_type = payload.get("type")
        principal_id = payload.get("sub")
        token_version = payload.get("token_version")
        if user_type == "admin":
            principals = await db.execute(select(Admins).where(Admins.admin_id == principal_id))
            principal = principals.scalars().first()
            if not principal:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found")
            if principal.token_version != token_version:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")
            return principal, True
        else:
            principals = await db.execute(select(Users).where(Users.user_id == principal_id))
            principal = principals.scalars().first()
            if not principal:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            if principal.token_version != token_version:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")
            return principal, False  
    except HTTPException as exception:
        raise exception
    except Exception as exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exception))
