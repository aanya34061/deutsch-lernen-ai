from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.config import settings
from app.database import check_db_health
from app.services.ollama_service import OllamaService
from app.services.storage_service import ObjectStorage

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("")
async def get_health():
    """Health check endpoint reporting backend, database, and AI service configuration."""
    db_health = await check_db_health()
    
    # Check Ollama status safely with short timeout
    ai_status = await OllamaService.check_status()
    ollama_status = ai_status.get("status") if ai_status.get("provider") in {"disabled", "hosted"} else ("online" if ai_status.get("is_ready") else (
        "offline" if not ai_status.get("is_running") else f"model_missing ({ai_status.get('configured_model')})"
    ))

    is_overall_healthy = db_health.get("status") == "connected"

    payload = {
        "status": "healthy" if is_overall_healthy else "degraded",
        "app_env": settings.APP_ENV,
        "database": db_health,
        "ai_engine": {
            "provider": ai_status.get("provider", settings.AI_PROVIDER),
            "model": ai_status.get("configured_model"),
            "embed_model": ai_status.get("configured_embed_model"),
            "status": ollama_status,
            "detailed_status": ai_status.get("status"),
            "is_ready": ai_status.get("is_ready"),
            "is_running": ai_status.get("is_running"),
            "model_available": ai_status.get("model_available"),
            **({"base_url": settings.OLLAMA_BASE_URL} if settings.APP_ENV.lower() != "production" and settings.AI_PROVIDER.lower() == "ollama" else {}),
            "setup_instructions": ai_status.get("setup_instructions")
        },
        "file_storage": {
            "provider": settings.STORAGE_PROVIDER,
            "configured": settings.STORAGE_PROVIDER.lower() == "local" or ObjectStorage.configured(),
            "persistent": settings.STORAGE_PROVIDER.lower() in {"s3", "r2", "s3-compatible", "vercel-blob"},
        },
        "speech": {
            "stt_provider": settings.STT_PROVIDER,
            "tts_provider": settings.TTS_PROVIDER
        },
        "error_monitoring": {"provider": "sentry", "configured": bool(settings.SENTRY_DSN)},
        "version": "1.0.0"
    }
    if settings.APP_ENV.lower() == "production" and (not is_overall_healthy or not ObjectStorage.configured()):
        return JSONResponse(status_code=503, content=payload)
    return payload
