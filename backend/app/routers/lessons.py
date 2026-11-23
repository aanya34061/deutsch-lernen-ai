from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, status
from app.models.lesson import (
    LessonSummary,
    LessonResponse,
    LessonCreateFromMaterial
)
from app.services.curriculum_service import CurriculumService

router = APIRouter(prefix="/lessons", tags=["German Lessons & Curriculum"])

@router.get("/modules")
async def list_curriculum_modules(level: Optional[str] = Query(None, description="Optional CEFR level: A1, A2, B1")):
    """Return published modules and their topic-to-lesson links from the manifest import."""
    return await CurriculumService.list_modules(level=level)

@router.get("", response_model=List[LessonSummary])
async def list_lessons(
    level: Optional[str] = Query(None, description="Filter by CEFR level: A1, A2, B1"),
    topic: Optional[str] = Query(None, description="Filter by topic keyword")
):
    """Retrieve structured German curriculum lessons for A1, A2, and B1."""
    return await CurriculumService.list_lessons(level=level, topic=topic)

@router.get("/{lesson_id}", response_model=LessonResponse)
async def get_lesson(lesson_id: str):
    """Retrieve full lesson content by ID."""
    lesson = await CurriculumService.get_lesson(lesson_id)
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lesson '{lesson_id}' not found"
        )
    return lesson

@router.post("/{lesson_id}/complete")
async def mark_lesson_completed(lesson_id: str):
    """Mark a lesson as completed."""
    success = await CurriculumService.mark_lesson_completed(lesson_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update lesson completion status"
        )
    return {"message": "Lesson marked as completed", "lesson_id": lesson_id, "is_completed": True}

@router.post("/from-material", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
async def create_lesson_from_material(data: LessonCreateFromMaterial):
    """Create a new study lesson from an uploaded Study Library material."""
    try:
        return await CurriculumService.create_lesson_from_material(
            material_id=data.material_id,
            title=data.title,
            cefr_level=data.cefr_level,
            topic=data.topic,
            module_title=data.module_title
        )
    except ValueError as e:
        code = status.HTTP_422_UNPROCESSABLE_CONTENT if "no extracted text" in str(e).lower() else status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=code, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not create a study page from this material. Please try again."
        )
