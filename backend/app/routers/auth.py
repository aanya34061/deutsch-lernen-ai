import hashlib
import hmac
import secrets
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from pymongo.errors import DuplicateKeyError

from app.config import settings
from app.database import get_db
from app.security import create_session, current_user, migrate_legacy_default_records

router = APIRouter(prefix="/auth", tags=["Authentication"])
_PASSWORD_ITERATIONS = 310_000


class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=40, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=12, max_length=128)
    name: Optional[str] = Field(default=None, min_length=1, max_length=80)


def _password_hash(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PASSWORD_ITERATIONS).hex()


def _set_auth_cookies(response: Response, token: str, csrf: str) -> None:
    secure = settings.APP_ENV.lower() == "production"
    common = {"secure": secure, "samesite": "strict", "path": "/", "max_age": settings.SESSION_TTL_DAYS * 86400}
    response.set_cookie(settings.SESSION_COOKIE_NAME, token, httponly=True, **common)
    response.set_cookie("deutsch_csrf", csrf, httponly=False, **common)


def _public_account(account: dict) -> dict:
    return {
        "id": str(account["_id"]),
        "username": account["username"],
        "name": account.get("name") or account["username"],
        "current_level": account.get("current_level", "A1"),
        "target_level": account.get("target_level", "B1"),
    }


def _set_csrf_cookie(response: Response, csrf: str) -> None:
    response.set_cookie(
        "deutsch_csrf", csrf, httponly=False, secure=settings.APP_ENV.lower() == "production",
        samesite="strict", path="/", max_age=settings.SESSION_TTL_DAYS * 86400,
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(data: Credentials, response: Response):
    username = data.username.strip().lower()
    salt = secrets.token_bytes(16)
    account = {
        "username": username,
        "name": (data.name or username).strip(),
        "password_salt": salt.hex(),
        "password_hash": _password_hash(data.password, salt),
        "password_iterations": _PASSWORD_ITERATIONS,
        "current_level": "A1",
        "target_level": "B1",
        "created_at": datetime.now(timezone.utc),
        "disabled": False,
    }
    try:
        result = await get_db().accounts.insert_one(account)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="That username is already registered.")
    account["_id"] = result.inserted_id
    await migrate_legacy_default_records(result.inserted_id)
    account = await get_db().accounts.find_one({"_id": result.inserted_id})
    token, csrf, _ = await create_session(result.inserted_id)
    _set_auth_cookies(response, token, csrf)
    return {**_public_account(account), "csrf_token": csrf}


@router.post("/login")
async def login(data: Credentials, response: Response):
    username = data.username.strip().lower()
    account = await get_db().accounts.find_one({"username": username, "disabled": {"$ne": True}})
    valid = False
    if account:
        try:
            salt = bytes.fromhex(account["password_salt"])
            actual = _password_hash(data.password, salt)
            valid = hmac.compare_digest(actual, account["password_hash"])
        except (KeyError, ValueError):
            valid = False
    if not valid:
        raise HTTPException(status_code=401, detail="Username or password is incorrect.")
    token, csrf, _ = await create_session(account["_id"])
    _set_auth_cookies(response, token, csrf)
    return {**_public_account(account), "csrf_token": csrf}


@router.get("/me")
async def me():
    return current_user()


@router.get("/csrf")
async def refresh_csrf(request: Request, response: Response):
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Please log in to continue.")
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    csrf = secrets.token_urlsafe(32)
    result = await get_db().sessions.update_one(
        {"token_hash": token_hash}, {"$set": {"csrf_hash": hashlib.sha256(csrf.encode("utf-8")).hexdigest()}}
    )
    if not result.matched_count:
        raise HTTPException(status_code=401, detail="Your session has expired. Please log in again.")
    _set_csrf_cookie(response, csrf)
    return {"csrf_token": csrf}


@router.post("/logout")
async def logout(request: Request, response: Response):
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if token:
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        await get_db().sessions.delete_one({"token_hash": token_hash})
    response.delete_cookie(settings.SESSION_COOKIE_NAME, path="/", secure=settings.APP_ENV.lower() == "production", httponly=True, samesite="strict")
    response.delete_cookie("deutsch_csrf", path="/", secure=settings.APP_ENV.lower() == "production", httponly=False, samesite="strict")
    return {"success": True}
