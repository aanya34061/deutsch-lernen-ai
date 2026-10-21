from fastapi import APIRouter
from app.config import settings
from app.database import check_db_health
from app.services.ollama_service import OllamaService

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("")
async def get_health():
    """Health check endpoint reporting backend, database, and AI service configuration."""
    db_health = await check_db_health()
    
    # Check Ollama status safely with short timeout
    ai_status = await OllamaService.check_status()
    ollama_status = "online" if ai_status.get("is_ready") else (
        "offline" if not ai_status.get("is_running") else f"model_missing ({ai_status.get('configured_model')})"
    )

    is_overall_healthy = db_health.get("status") == "connected"

    return {
        "status": "healthy" if is_overall_healthy else "degraded",
        "app_env": settings.APP_ENV,
        "database": db_health,
        "ai_engine": {
            "provider": "ollama",
            "model": settings.OLLAMA_MODEL,
            "embed_model": settings.OLLAMA_EMBED_MODEL,
            "status": ollama_status,
            "detailed_status": ai_status.get("status"),
            "is_ready": ai_status.get("is_ready"),
            "is_running": ai_status.get("is_running"),
            "model_available": ai_status.get("model_available"),
            "base_url": settings.OLLAMA_BASE_URL,
            "setup_instructions": ai_status.get("setup_instructions")
        },
        "speech": {
            "stt_provider": settings.STT_PROVIDER,
            "tts_provider": settings.TTS_PROVIDER
        },
        "version": "1.0.0"
    }
