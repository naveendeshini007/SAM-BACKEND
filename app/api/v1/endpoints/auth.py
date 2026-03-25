from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie, Request, Form
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_optional_current_principal, get_current_principal
from app.services.auth import (
    authenticate_and_login,
    change_password_service,
    refresh_service,
    logout_service,
)
from app.models.admins import Admins
from app.models.users import Users
from app.schemas.auth import LoginResponse, ChangePasswordRequest, RefreshResponse
from app.core.security import verify_password
from app.core.log_event import log_auth_event

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
    response: Response,
    username_or_email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        try:
            result = await authenticate_and_login(db, username_or_email, password)
        except Exception as exception:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exception))

        if result.get("error"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        # If require_password_change return that flag along with id/is_admin
        if result.get("require_password_change"):
            return LoginResponse(require_password_change=True, id=result.get("id"), is_admin=result.get("is_admin"))

        # set refresh cookie and return access token + id/is_admin
        response.set_cookie(
            key="refresh_token",
            value=result.get("refresh_token"),
            httponly=True,
            secure=False,
            samesite="lax",
            path="/api/v1/auth/refresh",
        )

        return LoginResponse(access_token=result.get("access_token"), id=result.get("id"), is_admin=result.get("is_admin"))
    except HTTPException as exception:
        raise exception
    except Exception as exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exception))


@router.post("/change-password")
async def change_password(
    req: ChangePasswordRequest,
    principal=Depends(get_optional_current_principal),
    db: AsyncSession = Depends(get_db),
):
    # principal is either (instance, is_admin) or (None, False)
    instance, is_admin = principal
    try:
        if instance:
            # authenticated path
            response = await change_password_service(db, instance, is_admin, req.old_password, req.new_password)
        else:
            # unauthenticated first-login path: require username_or_email and old_password
            if not req.username_or_email or not req.old_password:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="username_or_email and old_password are required for first-time password reset")
            # find principal by username_or_email
            check = await db.execute(select(Admins).where((Admins.username == req.username_or_email) | (Admins.email == req.username_or_email)))
            admin = check.scalars().first()
            user = None
            if not admin:
                check_non_admin = await db.execute(select(Users).where((Users.username == req.username_or_email) | (Users.email == req.username_or_email)))
                user = check_non_admin.scalars().first()

            target = admin or user
            if not target:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Principal not found")

            # verify the provided temporary/old password
            if not verify_password(req.old_password, target.password_hash):
                # log auth event
                await log_auth_event(db, "admin" if admin else "user", admin.admin_id if admin else user.user_id, "password_change", False, note="old password mismatch")
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid temporary password")

            # now perform password change and require current password validation
            response = await change_password_service(db, target, bool(admin), req.old_password, req.new_password, require_current_password=True)

    except HTTPException:
        raise
    except Exception as exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exception))

    if response.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response.get("error"))
    return {"ok": True}


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
):  
    try:
        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")

        try:
            tokens = await refresh_service(db, refresh_token)
        except Exception as exception:
            # refresh_service raises RuntimeError with details
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exception))

        response.set_cookie(
            key="refresh_token",
            value=tokens.get("refresh_token"),
            httponly=True,
            secure=False,
            samesite="lax",
            path="/api/v1/auth/refresh",
        )

        return RefreshResponse(access_token=tokens.get("access_token"))
    except HTTPException as exception:
        raise exception
    except Exception as exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exception))


@router.get("/me")
async def me(
    principal=Depends(get_current_principal),
):
    try:
        # principal is (instance, is_admin)
        instance, is_admin = principal
        pid = str(instance.admin_id) if is_admin else str(instance.user_id)
        return {
            "id": pid,
            "username": instance.username,
            "email": instance.email,
            "full_name": instance.full_name,
            "is_admin": is_admin,
        }
    except Exception as exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exception))


@router.post("/logout")
async def logout(
    response: Response,
    principal=Depends(get_current_principal),
    db: AsyncSession = Depends(get_db),
):
    instance, is_admin = principal
    try:
        await logout_service(db, instance, is_admin)
        response.delete_cookie("refresh_token", path="/api/v1/auth/refresh")
        return {"ok": True}
    except Exception as exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exception))
