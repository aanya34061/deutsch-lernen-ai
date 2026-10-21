import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status

from app.models.practice import (
    ReadingExerciseLearnerView,
    ReadingSubmissionRequest,
    ReadingSubmissionResponse,
    ListeningExerciseLearnerView,
    ListeningSubmissionRequest,
    ListeningSubmissionResponse,
    WritingPromptBase,
    WritingDraftRequest,
    WritingDraftResponse,
    WritingSubmissionRequest,
    WritingEvaluationResponse,
    SpeakingScenario,
    SpeakingSessionStartRequest,
    SpeakingMessageRequest,
    SpeakingMessageResponse,
    PracticeProgressResponse
)
from app.services.practice_service import PracticeService

logger = logging.getLogger("german_app.routers.practice")

router = APIRouter(prefix="/practice", tags=["Interactive Skills Practice (Phase 5)"])

# ==================== 1. Reading (Lesen) Endpoints ====================

@router.get("/reading", response_model=List[Dict[str, Any]])
async def list_reading_exercises(
    level: Optional[str] = Query(None, description="Filter by CEFR level: A1, A2, B1"),
    topic: Optional[str] = Query(None, description="Filter by topic keyword")
):
    """Retrieve reading passages list with metadata."""
    return await PracticeService.list_reading_exercises(cefr_level=level, topic=topic)

@router.get("/reading/{exercise_id}", response_model=ReadingExerciseLearnerView)
async def get_reading_exercise(exercise_id: str):
    """Retrieve a single reading exercise (hides solutions until submission)."""
    ex = await PracticeService.get_reading_exercise(exercise_id)
    if not ex:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reading exercise '{exercise_id}' not found."
        )
    return ex

@router.post("/reading/{exercise_id}/submit", response_model=ReadingSubmissionResponse)
async def submit_reading_answers(exercise_id: str, submission: ReadingSubmissionRequest):
    """Submit comprehension answers, calculate score, and reveal full translation and explanations."""
    try:
        if not await PracticeService.get_reading_exercise(exercise_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reading exercise '{exercise_id}' not found.")
        return await PracticeService.evaluate_reading_submission(
            exercise_id=exercise_id,
            user_answers=submission.answers,
            time_spent_seconds=submission.time_spent_seconds
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e))
    except Exception as e:
        logger.error("Reading submission failed (%s).", type(e).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Could not save reading attempt. Please try again.")

# ==================== 2. Listening (Hören) Endpoints ====================

@router.get("/listening", response_model=List[Dict[str, Any]])
async def list_listening_exercises(
    level: Optional[str] = Query(None, description="Filter by CEFR level: A1, A2, B1"),
    topic: Optional[str] = Query(None, description="Filter by topic keyword")
):
    """Retrieve listening audio exercises list."""
    return await PracticeService.list_listening_exercises(cefr_level=level, topic=topic)

@router.get("/listening/resources", response_model=List[Dict[str, Any]])
async def list_listening_resources(
    level: Optional[str] = Query(None, description="Filter external listening resources by A1, A2, or B1"),
    category: Optional[str] = Query(None, description="Filter by resource category"),
    search: Optional[str] = Query(None, description="Search title, topic, description, or publisher"),
):
    """Return the maintained external resource catalogue and persisted completion state."""
    if level and level.upper() not in {"A1", "A2", "B1"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Level must be A1, A2, or B1.")
    return await PracticeService.list_listening_resources(level, category, search)

@router.post("/listening/resources/{resource_id}/complete", response_model=Dict[str, Any])
async def complete_listening_resource(resource_id: str):
    """Persist a learner-confirmed completion of an external listening resource."""
    try:
        return await PracticeService.complete_listening_resource(resource_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("Listening resource completion failed (%s).", type(e).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Could not save listening completion. Please try again.")

@router.get("/listening/{exercise_id}", response_model=ListeningExerciseLearnerView)
async def get_listening_exercise(exercise_id: str):
    """Retrieve a single listening exercise (audio script and translation hidden by default)."""
    ex = await PracticeService.get_listening_exercise(exercise_id)
    if not ex:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listening exercise '{exercise_id}' not found."
        )
    return ex

@router.post("/listening/{exercise_id}/submit", response_model=ListeningSubmissionResponse)
async def submit_listening_answers(exercise_id: str, submission: ListeningSubmissionRequest):
    """Submit listening comprehension answers, score attempt, and reveal script & translation."""
    try:
        return await PracticeService.evaluate_listening_submission(
            exercise_id=exercise_id,
            user_answers=submission.answers,
            time_spent_seconds=submission.time_spent_seconds
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("Listening submission failed (%s).", type(e).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Could not save listening attempt. Please try again.")

# ==================== 3. Writing (Schreiben) Endpoints ====================

@router.get("/writing/prompts", response_model=List[WritingPromptBase])
async def list_writing_prompts(
    level: Optional[str] = Query(None, description="Filter by CEFR level: A1, A2, B1"),
    topic: Optional[str] = Query(None, description="Filter by topic keyword"),
    task_type: Optional[str] = Query(None, description="Filter by task type")
):
    """Retrieve writing prompts for emails, invitations, routines, and opinions."""
    return await PracticeService.list_writing_prompts(cefr_level=level, topic=topic, task_type=task_type)

@router.get("/writing/prompts/{prompt_id}", response_model=WritingPromptBase)
async def get_writing_prompt(prompt_id: str):
    """Retrieve details for a single writing prompt."""
    prompt = await PracticeService.get_writing_prompt(prompt_id)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Writing prompt '{prompt_id}' not found."
        )
    return prompt

@router.get("/writing/drafts/{prompt_id}", response_model=Optional[WritingDraftResponse])
async def get_writing_draft(prompt_id: str):
    """Retrieve saved draft for a prompt."""
    draft = await PracticeService.get_writing_draft(prompt_id)
    if not draft:
        return None
    return draft

@router.post("/writing/drafts", response_model=WritingDraftResponse)
async def save_writing_draft(req: WritingDraftRequest):
    """Save an unfinished writing draft."""
    return await PracticeService.save_writing_draft(prompt_id=req.prompt_id, content=req.content)

@router.delete("/writing/drafts/{draft_id}")
async def delete_writing_draft(draft_id: str):
    """Delete a saved draft."""
    deleted = await PracticeService.delete_writing_draft(draft_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found.")
    return {"message": "Draft deleted successfully"}

@router.post("/writing/evaluate", response_model=WritingEvaluationResponse)
async def evaluate_writing_submission(req: WritingSubmissionRequest):
    """
    Evaluate learner's German writing response with local AI Tutor (or rule-based fallback).
    Returns corrections, grammar mistakes, word order, spelling, and suggestions.
    """
    try:
        return await PracticeService.evaluate_writing_submission(
            prompt_id=req.prompt_id,
            content=req.content,
            cefr_level=req.cefr_level,
            time_spent_seconds=req.time_spent_seconds
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Writing submission failed (%s).", type(e).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Could not save writing submission. Please try again.")

@router.get("/writing/submissions", response_model=List[WritingEvaluationResponse])
async def list_writing_submissions(
    prompt_id: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=50)
):
    """Retrieve previous writing submissions with feedback."""
    return await PracticeService.list_writing_submissions(prompt_id=prompt_id, limit=limit)

# ==================== 4. Speaking (Sprechen) Endpoints ====================

@router.get("/speaking/scenarios", response_model=List[SpeakingScenario])
async def list_speaking_scenarios(
    level: Optional[str] = Query(None, description="Filter by CEFR level: A1, A2, B1"),
    topic: Optional[str] = Query(None, description="Filter by topic keyword")
):
    """List interactive speaking and role-play scenarios."""
    return await PracticeService.list_speaking_scenarios(cefr_level=level, topic=topic)

@router.post("/speaking/sessions", response_model=SpeakingMessageResponse)
async def start_speaking_session(req: SpeakingSessionStartRequest):
    """Start an interactive German speaking session with initial tutor greeting."""
    try:
        return await PracticeService.start_speaking_session(
            scenario_id=req.scenario_id,
            cefr_level=req.cefr_level,
            topic=req.topic
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("Speaking session start failed (%s).", type(e).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Could not start speaking session.")

@router.get("/speaking/sessions/{session_id}")
async def get_speaking_session(session_id: str):
    """Retrieve conversation history for an active speaking session."""
    session = await PracticeService.get_speaking_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Speaking session not found.")
    return session

@router.post("/speaking/sessions/{session_id}/message", response_model=SpeakingMessageResponse)
async def send_speaking_message(session_id: str, req: SpeakingMessageRequest):
    """Send learner speech/text turn and receive next tutor reply with corrections."""
    try:
        return await PracticeService.send_speaking_message(
            session_id=session_id,
            message=req.message,
            audio_url=req.audio_url
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Speaking turn failed (%s).", type(e).__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="The speaking service is unavailable. Your message was not confirmed; please try again.")

# ==================== 5. Practice Progress & Analytics ====================

@router.get("/progress", response_model=PracticeProgressResponse)
async def get_practice_progress():
    """Retrieve comprehensive practice progress across Lesen, Hören, Schreiben, and Sprechen."""
    return await PracticeService.get_practice_progress()
