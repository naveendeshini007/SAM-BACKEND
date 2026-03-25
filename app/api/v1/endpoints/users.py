from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_admin
from app.services.users import create_user_service, list_auth_events
from app.schemas.users import UserCreate
from fastapi import HTTPException, status


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
async def list_events(admin=Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    try:
        return await list_auth_events(db)
    except RuntimeError as exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exception))
