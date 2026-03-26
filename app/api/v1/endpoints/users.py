from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_admin
from app.services.users import create_user_service, list_auth_events, list_users_service, get_user_service, soft_delete_user_service
from app.schemas.users import UserCreate


router = APIRouter()

# FUTURE COGNITO/MESSAGING MIGRATION:
# - Instead of storing password locally, create user in Cognito and return/ email temporary password
# - Use AWS SES or another email provider to send temp password; do not return temp_password in production
# - Replace local JWT rotation with Cognito refresh token handling


@router.post("/")
async def create_user(
    payload: UserCreate,
    admin=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        response = await create_user_service(db, admin, payload)
        return response
    except RuntimeError as exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exception))
    except Exception as exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exception))


@router.get("/events")
async def list_events(
    admin=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, description="Max number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
):
    try:
        return await list_auth_events(db, limit=limit, offset=offset)
    except RuntimeError as exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exception))


@router.get("/")
async def list_users(
    admin=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, description="Max number of users to return"),
    offset: int = Query(0, ge=0, description="Number of users to skip"),
):
    try:
        return await list_users_service(db, limit=limit, offset=offset)
    except RuntimeError as exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exception))


@router.get("/{user_id}")
async def get_user(user_id: str, admin=Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    try:
        user = await get_user_service(db, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user
    except RuntimeError as exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exception))


@router.delete("/{user_id}")
async def deactivate_user(user_id: str, admin=Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    try:
        return await soft_delete_user_service(db, admin, user_id)
    except RuntimeError as exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exception))
