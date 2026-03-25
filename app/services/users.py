"""User lifecycle service implementations.

This module implements user management functions (create user, list auth
events). Endpoints should import from `app.services.users` so service names
align with resource names.
"""
from typing import Dict
import uuid

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import Users
from app.core.security import hash_password, generate_temp_password
from app.core.log_event import log_auth_event


async def create_user_service(db: AsyncSession, admin, payload) -> Dict:
	"""Create a new user record with a temporary password and log the event.

	Returns a dict containing the created user info and the generated
	temporary password (used in local/dev flows). In production this
	temporary password should be emailed and not returned in the API.
	"""
	try:
		temp_password = generate_temp_password()
		pwd_hash = hash_password(temp_password)
		user_id = uuid.uuid4()
		stmt = insert(Users).values(
			user_id=user_id,
			username=payload.username,
			email=payload.email,
			full_name=payload.full_name,
			password_hash=pwd_hash,
			must_change_password=True,
			is_active=True,
			created_by_admin_id=admin.admin_id,
		)
		await db.execute(stmt)
		await db.commit()
		await log_auth_event(db, "admin", admin.admin_id, "user_created", True, note=f"created user {payload.email}")
		return {"user_id": str(user_id), "username": payload.username, "email": payload.email, "full_name": payload.full_name, "temp_password": temp_password}
	except Exception as exc:
		raise RuntimeError(f"create_user_service failed: {exc}")


async def list_auth_events(db: AsyncSession, limit: int = 100):
	try:
		from sqlalchemy import desc
		from app.models.auth_events import AuthEvents

		auth_events = await db.execute(select(AuthEvents).order_by(desc(AuthEvents.happened_at)).limit(limit))
		rows = auth_events.scalars().all()
		result = []
		for r in rows:
			result.append({
				"auth_event_id": str(r.auth_event_id),
				"app_user_type": r.app_user_type,
				"app_user_id": str(r.app_user_id),
				"event_type": r.event_type,
				"note": r.note,
				"success": r.success,
				"happened_at": r.happened_at.isoformat() if r.happened_at else None,
				"session_id": str(r.session_id) if r.session_id else None,
				"related_event_id": str(r.related_event_id) if r.related_event_id else None,
			})
		return result
	except Exception as exc:
		raise RuntimeError(f"list_auth_events failed: {exc}")


__all__ = ["create_user_service", "list_auth_events"]
