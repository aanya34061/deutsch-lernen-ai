import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field
from pymongo.errors import PyMongoError

from app.models.conversation import ConversationResponse, ConversationSummary
from app.models.exercise import ExerciseLearnerView
from app.services.ollama_service import (
    OllamaService,
    OllamaNotRunningError,
    OllamaModelMissingError,
    OllamaTimeoutError,
    OllamaError
)
from app.services.retrieval_service import RetrievalService
from app.services.tutor_service import TutorService
from app.services.ai_exercise_service import AiExerciseService

logger = logging.getLogger("german_app.routers.tutor")

router = APIRouter(prefix="/tutor", tags=["AI German Tutor & RAG"])

class TutorChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="Learner question or sentence")
    conversation_id: Optional[str] = Field(None, description="Optional existing conversation ID")
    cefr_level: str = Field("A1", description="CEFR level: A1, A2, B1")
    material_id: Optional[str] = Field(None, description="Optional specific Study Library material to ground in")
    lesson_id: Optional[str] = Field(None, description="Optional related curriculum lesson")
    response_language: str = Field("english", description="Explanation language: english, german, bilingual")

class TutorChatResponse(BaseModel):
    conversation_id: str
    message: str
    role: str = "assistant"
    sources: List[Dict[str, Any]] = []
    is_rag: bool = False
    cefr_level: str = "A1"
    created_at: Optional[str] = None

class TutorExerciseGenerateRequest(BaseModel):
    lesson_id: Optional[str] = None
    material_id: Optional[str] = None
    cefr_level: str = "A1"
    count: int = Field(3, ge=1, le=5)

# 1. AI Tutor Status
@router.get("/status")
async def get_tutor_status():
    """
    Check Ollama connection, configured chat and embedding models,
    and library indexing statistics. Never crashes if Ollama is offline.
    """
    try:
        ollama_status = await OllamaService.check_status()
        indexing_status = await RetrievalService.get_index_status()
        return {
            **ollama_status,
            "indexing": indexing_status
        }
    except Exception as e:
        logger.error(f"Error checking tutor status: {e}")
        return {
            "status": "error",
            "is_ready": False,
            "is_running": False,
            "message": str(e),
            "indexing": None
        }

# 2. Chat with Tutor (RAG-grounded)
@router.post("/chat", response_model=TutorChatResponse)
async def chat_with_tutor(req: TutorChatRequest):
    """
    Submit a question or sentence to the AI German Tutor.
    Retrieves grounded context from uploaded notes, respects CEFR level,
    and returns explanations, corrections, and citations.
    """
    try:
        result = await TutorService.chat(
            message=req.message,
            conversation_id=req.conversation_id,
            cefr_level=req.cefr_level,
            material_id=req.material_id,
            lesson_id=req.lesson_id,
            response_language=req.response_language
        )
        return TutorChatResponse(**result)

    except (OllamaNotRunningError, OllamaModelMissingError) as ai_err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(ai_err)
        )
    except OllamaTimeoutError as timeout_err:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(timeout_err)
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except (RuntimeError, PyMongoError) as db_err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable. The tutor request was not saved.") from db_err
    except OllamaError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The local AI service could not complete this request. Please try again."
        )
    except Exception as e:
        logger.error("Unexpected tutor chat error (%s).", type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The tutor could not complete this request. Please try again."
        )

# 3. List Conversations
@router.get("/conversations", response_model=List[ConversationSummary])
async def list_conversations(user_id: Optional[str] = Query(None)):
    """Retrieve list of previous tutor conversations."""
    try:
        return await TutorService.list_conversations(user_id=user_id)
    except Exception as e:
        logger.error(f"Failed to list conversations: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Could not load saved tutor conversations.")

# 4. Get Single Conversation
@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str):
    """Retrieve a single conversation history by ID."""
    conv = await TutorService.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found."
        )
    return conv

# 5. Delete Conversation
@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation history."""
    deleted = await TutorService.delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found or already deleted."
        )
    return {"message": "Conversation deleted successfully", "id": conversation_id}

# 6. Index Status
@router.get("/index/status")
async def get_index_status():
    """Get aggregated stats on knowledge chunks and indexing status."""
    return await RetrievalService.get_index_status()

# 7. Rebuild / Reindex All Materials
@router.post("/index/rebuild")
async def rebuild_index(force: bool = Query(False, description="Force re-embedding even if content hash matches")):
    """Re-index all Study Library materials with extracted text."""
    try:
        return await RetrievalService.rebuild_all_indexes(force=force)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Could not rebuild the document index. Please try again.")

# 8. Retry Indexing a Single Material
@router.post("/index/retry/{material_id}")
async def retry_index_material(material_id: str):
    """Retry indexing a failed or un-indexed material."""
    try:
        res = await RetrievalService.index_material(material_id, force=True)
        return res
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_err))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Could not index this material. Please try again.")

# 9. AI-Generated Practice Exercises
@router.post("/exercises/generate", response_model=List[ExerciseLearnerView])
async def generate_exercises(req: TutorExerciseGenerateRequest):
    """
    Generate 1-5 validated practice questions based on a lesson or uploaded document.
    Saves exercises in the database and returns learner views ready for ExerciseRunner.
    """
    try:
        return await AiExerciseService.generate_exercises(
            lesson_id=req.lesson_id,
            material_id=req.material_id,
            cefr_level=req.cefr_level,
            count=req.count
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        logger.error("Exercise generation failed (%s).", type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Exercise generation is unavailable. Please try again later."
        )
