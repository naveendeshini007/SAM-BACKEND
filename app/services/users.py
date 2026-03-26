from typing import Dict
import uuid
from sqlalchemy import insert, select, update, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.users import Users
from app.core.security import hash_password, generate_temp_password
from app.core.log_event import log_auth_event
from app.models.auth_events import AuthEvents


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
	except Exception as exception:
		raise RuntimeError(f"create_user_service failed: {exception}")


async def list_auth_events(db: AsyncSession, limit: int = 100, offset: int = 0):
	try:
		auth_events = await db.execute(select(AuthEvents).order_by(desc(AuthEvents.happened_at)).limit(limit).offset(offset))
		rows = auth_events.scalars().all()
		result = []
		for row in rows:
			result.append({
				"auth_event_id": str(row.auth_event_id),
				"app_user_type": row.app_user_type,
				"app_user_id": str(row.app_user_id),
				"event_type": row.event_type,
				"note": row.note,
				"success": row.success,
				"happened_at": row.happened_at.isoformat() if row.happened_at else None,
				"session_id": str(row.session_id) if row.session_id else None,
				"related_event_id": str(row.related_event_id) if row.related_event_id else None,
			})
		return result
	except Exception as exception:
		raise RuntimeError(f"list_auth_events failed: {exception}")





async def list_users_service(db: AsyncSession, limit: int = 100, offset: int = 0):
	try:
		users = await db.execute(select(Users).limit(limit).offset(offset))
		rows = users.scalars().all()
		result = []
		for user in rows:
			result.append({
				"user_id": str(user.user_id),
				"username": user.username,
				"email": user.email,
				"full_name": user.full_name,
				"must_change_password": bool(user.must_change_password),
				"is_active": bool(user.is_active),
				"created_by_admin_id": str(user.created_by_admin_id) if user.created_by_admin_id else None,
				"last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
				"created_at": user.created_at.isoformat() if user.created_at else None,
			})
		return result
	except Exception as exception:
		raise RuntimeError(f"list_users_service failed: {exception}")


async def get_user_service(db: AsyncSession, user_id: str):
	try:
		uid = uuid.UUID(user_id)
		user_selected = await db.execute(select(Users).where(Users.user_id == uid))
		user = user_selected.scalars().first()
		if not user:
			return None
		return {
			"user_id": str(user.user_id),
			"username": user.username,
			"email": user.email,
			"full_name": user.full_name,
			"must_change_password": bool(user.must_change_password),
			"is_active": bool(user.is_active),
			"created_by_admin_id": str(user.created_by_admin_id) if user.created_by_admin_id else None,
			"last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
			"created_at": user.created_at.isoformat() if user.created_at else None,
		}
	except Exception as exception:
		raise RuntimeError(f"get_user_service failed: {exception}")


async def soft_delete_user_service(db: AsyncSession, admin, user_id: str):
	"""Soft-delete (deactivate) a user by setting is_active=False and rotating token_version."""
	try:
		uid = uuid.UUID(user_id)
		# set is_active = False and bump token_version to invalidate refresh tokens
		stmt = (
			update(Users)
			.where(Users.user_id == uid)
			.values(is_active=False, token_version=Users.token_version + 1)
		)
		await db.execute(stmt)
		await db.commit()
		await log_auth_event(db, "admin", admin.admin_id, "user_deactivated", True, note=f"deactivated user {user_id}")
		return {"ok": True}
	except Exception as exception:
		raise RuntimeError(f"soft_delete_user_service failed: {exception}")


__all__ = [
	"create_user_service",
	"list_auth_events",
	"list_users_service",
	"get_user_service",
	"soft_delete_user_service",
]
