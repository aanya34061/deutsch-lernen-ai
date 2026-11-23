import logging
from contextlib import asynccontextmanager
from urllib.parse import urlsplit
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo.errors import PyMongoError
from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection
from app.routers import auth, health, dashboard, levels, library, lessons, exercises, vocabulary, tutor, practice, study
from app.security import authenticate_request, reset_request_user
from app.services.storage_service import ObjectStorage
from app.rate_limit import enforce_request_limit

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("german_app")
API_V1_PREFIX = "/api/v1"


def _scrub_sentry_event(event, _hint):
    """Send stack traces without learner input, request data, or credentials."""
    event.pop("request", None)
    event.pop("user", None)
    for value in event.get("exception", {}).get("values", []):
        value["value"] = "Application exception"
        for frame in value.get("stacktrace", {}).get("frames", []):
            frame.pop("vars", None)
    return event


if settings.SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.SENTRY_ENVIRONMENT or settings.APP_ENV,
            integrations=[StarletteIntegration(), FastApiIntegration()],
            send_default_pii=False,
            traces_sample_rate=0.0,
            before_send=_scrub_sentry_event,
        )
        logger.info("External error monitoring is enabled.")
    except ImportError:
        logger.error("SENTRY_DSN is configured but sentry-sdk is not installed.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting German Learning App API...")
    if settings.APP_ENV.lower() == "production" and not ObjectStorage.configured():
        raise RuntimeError("Production requires configured persistent file storage credentials.")
    await connect_to_mongo()
    yield
    # Shutdown
    logger.info("Shutting down German Learning App API...")
    await close_mongo_connection()

app = FastAPI(
    title="German Learning App API",
    description="API for German Language Learning (A1-C2) with AI Tutoring, RAG, and Speech",
    version="1.0.0",
    lifespan=lifespan
)

@app.exception_handler(RuntimeError)
async def handle_runtime_error(request, exc: RuntimeError):
    message = str(exc)
    if "database connection not initialized" in message.lower():
        return JSONResponse(status_code=503, content={"detail": "Database unavailable. Check MongoDB and try again."})
    logger.exception("Unhandled runtime error", exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "The request could not be completed."})

@app.exception_handler(PyMongoError)
async def handle_database_error(request, exc: PyMongoError):
    logger.error("Database operation failed: %s", exc)
    return JSONResponse(status_code=503, content={"detail": "Database unavailable. No changes were confirmed; please retry."})

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def learner_session_middleware(request: Request, call_next):
    if request.url.path.startswith(API_V1_PREFIX) and request.method != "OPTIONS":
        allowed, retry_after = await enforce_request_limit(request)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please wait and try again."},
                headers={"Retry-After": str(retry_after)},
            )
        origin = request.headers.get("origin")
        if origin:
            request_origin = f"{request.url.scheme}://{request.url.netloc}"
            parsed_origin = urlsplit(origin)
            normalized_origin = f"{parsed_origin.scheme}://{parsed_origin.netloc}"
            if normalized_origin != request_origin and normalized_origin not in settings.cors_origin_list:
                return JSONResponse(status_code=403, content={"detail": "Request origin is not allowed."})
        try:
            _, user_id_token, user_token = await authenticate_request(request)
        except HTTPException as exc:
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=exc.headers)
        try:
            return await call_next(request)
        finally:
            reset_request_user((user_id_token, user_token))
    return await call_next(request)

# Versioned API Router
app.include_router(auth.router, prefix=API_V1_PREFIX)
app.include_router(health.router, prefix=API_V1_PREFIX)
app.include_router(dashboard.router, prefix=API_V1_PREFIX)
app.include_router(levels.router, prefix=API_V1_PREFIX)
app.include_router(library.router, prefix=API_V1_PREFIX)
app.include_router(lessons.router, prefix=API_V1_PREFIX)
app.include_router(exercises.router, prefix=API_V1_PREFIX)
app.include_router(vocabulary.router, prefix=API_V1_PREFIX)
app.include_router(tutor.router, prefix=API_V1_PREFIX)
app.include_router(practice.router, prefix=API_V1_PREFIX)
app.include_router(study.router, prefix=API_V1_PREFIX)

@app.get("/")
async def root():
    return {
        "app": "German Learning App API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_check": f"{API_V1_PREFIX}/health",
        "dashboard_summary": f"{API_V1_PREFIX}/dashboard"
    }
