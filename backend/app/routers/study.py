from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.study_service import StudyService

router = APIRouter(prefix="/study", tags=["Personal Notes & Question Bank"])


class NotesUpdate(BaseModel):
    markdown: str = Field(min_length=1, max_length=50000)


@router.get("/notes")
async def list_notes(material_id: Optional[str] = None):
    return await StudyService.list_notes(material_id)


@router.get("/notes/{note_id}")
async def get_note(note_id: str):
    try:
        return await StudyService.get_note(note_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.put("/notes/{note_id}")
async def save_note(note_id: str, update: NotesUpdate):
    try:
        return await StudyService.save_notes(note_id, update.markdown)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/notes/{note_id}/regenerate")
async def regenerate_note(note_id: str):
    try:
        return await StudyService.regenerate_notes(note_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Could not regenerate notes: {exc}")


@router.delete("/notes/{note_id}")
async def delete_note(note_id: str):
    try:
        await StudyService.delete_note(note_id)
        return {"success": True, "deleted_id": note_id}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/questions")
async def list_questions(
    material_id: Optional[str] = None,
    cefr_level: Optional[str] = None,
    topic: Optional[str] = None,
    difficulty: Optional[str] = None,
    question_type: Optional[str] = None,
    skill: Optional[str] = None,
    incorrect_only: bool = False,
):
    return await StudyService.list_questions(material_id, cefr_level, topic, difficulty, question_type, skill, incorrect_only)
