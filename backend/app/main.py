import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo.errors import PyMongoError
from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection
from app.routers import health, dashboard, levels, library, lessons, exercises, vocabulary, tutor, practice

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("german_app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting German Learning App API...")
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

# Versioned API Router
API_V1_PREFIX = "/api/v1"
app.include_router(health.router, prefix=API_V1_PREFIX)
app.include_router(dashboard.router, prefix=API_V1_PREFIX)
app.include_router(levels.router, prefix=API_V1_PREFIX)
app.include_router(library.router, prefix=API_V1_PREFIX)
app.include_router(lessons.router, prefix=API_V1_PREFIX)
app.include_router(exercises.router, prefix=API_V1_PREFIX)
app.include_router(vocabulary.router, prefix=API_V1_PREFIX)
app.include_router(tutor.router, prefix=API_V1_PREFIX)
app.include_router(practice.router, prefix=API_V1_PREFIX)

@app.get("/")
async def root():
    return {
        "app": "German Learning App API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_check": f"{API_V1_PREFIX}/health",
        "dashboard_summary": f"{API_V1_PREFIX}/dashboard"
    }
