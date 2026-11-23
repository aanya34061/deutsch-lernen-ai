import contextvars
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, Request, status

from app.config import settings
from app.database import get_db

_current_user_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("current_user_id", default=None)
_current_user: contextvars.ContextVar[Optional[dict]] = contextvars.ContextVar("current_user", default=None)


def current_user_id() -> str:
    value = _current_user_id.get()
    if not value:
        raise RuntimeError("Authenticated learner context is unavailable")
    return value


def current_user() -> dict:
    value = _current_user.get()
    if not value:
        raise RuntimeError("Authenticated learner context is unavailable")
    return value


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def authenticate_request(request: Request) -> tuple[Optional[dict], Optional[contextvars.Token], Optional[contextvars.Token]]:
    path = request.url.path
    if path in {"/api/v1/health", "/api/v1/auth/register", "/api/v1/auth/login"}:
        return None, None, None

    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please log in to continue.")
    session = await get_db().sessions.find_one({
        "token_hash": _token_hash(token),
        "expires_at": {"$gt": datetime.now(timezone.utc)},
    })
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Your session has expired. Please log in again.")

    origin = request.headers.get("origin")
    if origin and origin.rstrip("/") not in settings.cors_origin_list:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Request origin is not allowed.")
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        csrf_cookie = request.cookies.get("deutsch_csrf")
        csrf_header = request.headers.get("x-csrf-token")
        csrf_hash = _token_hash(csrf_header or "")
        if (
            not csrf_cookie or not csrf_header
            or not hmac.compare_digest(csrf_cookie, csrf_header)
            or not hmac.compare_digest(session.get("csrf_hash", ""), csrf_hash)
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Request verification failed. Refresh and try again.")

    account = await get_db().accounts.find_one({"_id": session["account_id"], "disabled": {"$ne": True}})
    if not account:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is unavailable. Please log in again.")
    user = {
        "id": str(account["_id"]),
        "username": account["username"],
        "name": account.get("name") or account["username"],
        "current_level": account.get("current_level", "A1"),
        "target_level": account.get("target_level", "B1"),
    }
    return user, _current_user_id.set(user["id"]), _current_user.set(user)


def reset_request_user(tokens: tuple[Optional[contextvars.Token], Optional[contextvars.Token]]) -> None:
    user_id_token, user_token = tokens
    if user_id_token is not None:
        _current_user_id.reset(user_id_token)
    if user_token is not None:
        _current_user.reset(user_token)


async def run_as_user(user_id: str, callback, *args, **kwargs):
    user_id_token = _current_user_id.set(user_id)
    user_token = _current_user.set({"id": user_id})
    try:
        return await callback(*args, **kwargs)
    finally:
        _current_user_id.reset(user_id_token)
        _current_user.reset(user_token)


async def create_session(account_id) -> tuple[str, str, datetime]:
    token = secrets.token_urlsafe(48)
    csrf = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.SESSION_TTL_DAYS)
    await get_db().sessions.insert_one({
        "account_id": account_id,
        "token_hash": _token_hash(token),
        "csrf_hash": _token_hash(csrf),
        "created_at": datetime.now(timezone.utc),
        "expires_at": expires_at,
    })
    return token, csrf, expires_at


async def migrate_legacy_default_records(account_id) -> None:
    """Assign pre-auth single-learner activity to the first registered account without deleting it."""
    db = get_db()
    owner = await db.auth_migrations.find_one_and_update(
        {"_id": "legacy_default_owner"},
        {"$setOnInsert": {"account_id": account_id, "created_at": datetime.now(timezone.utc)}},
        upsert=True,
        return_document=True,
    )
    if owner and owner.get("account_id") != account_id:
        return
    user_id = str(account_id)
    legacy_profile = await db.users.find_one({"username": "learner", "is_seeded": False})
    if legacy_profile:
        await db.accounts.update_one({"_id": account_id}, {"$set": {
            "current_level": legacy_profile.get("current_level", "A1"),
            "target_level": legacy_profile.get("target_level", "B1"),
            "daily_goal_minutes": legacy_profile.get("daily_goal_minutes", 20),
        }})
    for collection_name in (
        "materials", "vocabulary", "progress", "exercise_attempts", "conversations",
        "knowledge_chunks", "study_notes", "exercises", "writing_drafts",
        "writing_submissions", "speaking_sessions", "listening_resource_completions", "lessons",
    ):
        collection = db[collection_name]
        await collection.update_many(
            {"user_id": "default", "is_seeded": {"$ne": True}},
            {"$set": {"user_id": user_id}},
        )
    await db.lessons.update_many(
        {"user_id": {"$exists": False}}, {"$set": {"user_id": user_id}}
    )
    await db.exercises.update_many(
        {"user_id": {"$exists": False}, "is_seeded": {"$ne": True}},
        {"$set": {"user_id": user_id}},
    )
    owned_materials = await db.materials.find({"user_id": user_id}, {"_id": 1}).to_list(length=10000)
    material_ids = [str(item["_id"]) for item in owned_materials]
    if material_ids:
        await db.knowledge_chunks.update_many(
            {"material_id": {"$in": material_ids}, "user_id": {"$in": ["default", None]}},
            {"$set": {"user_id": user_id}},
        )
