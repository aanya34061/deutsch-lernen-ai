"""Shared, database-backed request limits for expensive/public endpoints."""
import hashlib
import logging
import math
import os
import time
from datetime import datetime, timedelta, timezone

from fastapi import Request
from pymongo.errors import PyMongoError

from app.database import get_db
from app.config import settings

logger = logging.getLogger("german_app.rate_limit")

# Fixed-window limits are shared across Vercel instances through MongoDB.
LIMITS = {
    "auth": (10, 60),
    "upload": (8, 60),
    "ai": (12, 60),
}


def category_for(path: str) -> str | None:
    if path in {"/api/v1/auth/register", "/api/v1/auth/login"}:
        return "auth"
    if path == "/api/v1/library/upload":
        return "upload"
    if path == "/api/v1/library/links":
        return "upload"
    if path.startswith("/api/v1/library/") and path.endswith("/process/retry"):
        return "ai"
    if path.startswith("/api/v1/study/notes/") and path.endswith("/regenerate"):
        return "ai"
    if path.startswith("/api/v1/tutor/") and path.endswith(("/chat", "/generate")):
        return "ai"
    if path in {
        "/api/v1/practice/writing/evaluate",
        "/api/v1/practice/speaking/sessions",
    } or path.startswith("/api/v1/practice/speaking/sessions/"):
        return "ai"
    return None


def client_key(request: Request) -> str:
    # Vercel overwrites x-forwarded-for at its edge. Do not trust arbitrary
    # forwarded headers from non-Vercel deployments.
    forwarded = request.headers.get("x-vercel-forwarded-for") if os.environ.get("VERCEL") == "1" else None
    remote = forwarded.split(",", 1)[0].strip() if forwarded else (request.client.host if request.client else "unknown")
    return hashlib.sha256(remote.encode("utf-8", errors="replace")).hexdigest()


async def enforce_request_limit(request: Request) -> tuple[bool, int]:
    category = category_for(request.url.path)
    if category is None:
        return True, 0
    limit, period = LIMITS[category]
    now = int(time.time())
    window = now // period
    bucket_id = f"{settings.MONGODB_DB_NAME}:{category}:{client_key(request)}:{window}"
    expires_at = datetime.fromtimestamp((window + 2) * period, timezone.utc)
    try:
        bucket = await get_db().request_limits.find_one_and_update(
            {"_id": bucket_id},
            {"$inc": {"count": 1}, "$setOnInsert": {"expires_at": expires_at}},
            upsert=True,
            return_document=True,
        )
    except PyMongoError:
        # A failed limit store must not silently turn off bot protection.
        logger.error("Request limit storage unavailable")
        raise
    count = int((bucket or {}).get("count", 1))
    return count <= limit, max(1, math.ceil((window + 1) * period - now))
