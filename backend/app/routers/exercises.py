from typing import Optional
from fastapi import APIRouter, HTTPException, status
from app.models.exercise import (
    ExerciseLearnerView,
    ExerciseSubmissionRequest,
    ExerciseSubmissionResponse
)
from app.services.exercise_service import ExerciseService

router = APIRouter(prefix="/exercises", tags=["Practice Engine & Exercises"])

@router.get("/{exercise_id}", response_model=ExerciseLearnerView)
async def get_exercise(exercise_id: str):
    """Retrieve exercise view for learner without revealing correct answers."""
    view = await ExerciseService.get_learner_view(exercise_id)
    if not view:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exercise '{exercise_id}' not found"
        )
    return view

@router.post("/{exercise_id}/submit", response_model=ExerciseSubmissionResponse)
async def submit_exercise_answer(exercise_id: str, submission: ExerciseSubmissionRequest):
    """
    Submit and evaluate an answer for any of the 6 question types:
    multiple_choice, fill_blank, translate, sentence_order, matching, true_false.
    Returns correctness, score, explanation, and correct German sentence.
    """
    try:
        return await ExerciseService.evaluate_submission(
            exercise_id=exercise_id,
            user_answer=submission.user_answer
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not save this exercise attempt. Please try again."
        )
