import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert
from app.models.auth_events import AuthEvents


async def log_auth_event(
    db: AsyncSession,
    app_user_type: str,
    app_user_id: uuid.UUID,
    event_type: str,
    success: bool,
    note: Optional[str] = None,
    session_id: Optional[uuid.UUID] = None,
    related_event_id: Optional[uuid.UUID] = None,
):
    stmt = insert(AuthEvents).values(
        auth_event_id=uuid.uuid4(),
        app_user_type=app_user_type,
        app_user_id=app_user_id,
        event_type=event_type,
        note=note,
        success=success,
        happened_at=datetime.utcnow(),
        session_id=session_id,
        related_event_id=related_event_id,
    )
    await db.execute(stmt)
    await db.commit()
