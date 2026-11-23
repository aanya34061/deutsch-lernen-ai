from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Query, status
from app.models.vocabulary import (
    VocabularyCreate,
    VocabularyBatchCreate,
    VocabularyUpdate,
    VocabularyResponse,
    ExtractVocabularyResponse
)
from app.services.vocabulary_service import VocabularyService
from app.database import get_db
from app.security import current_user_id
from bson import ObjectId

router = APIRouter(prefix="/vocabulary", tags=["Vocabulary Management"])

class ExtractFromMaterialRequest(BaseModel):
    material_id: Optional[str] = None
    text: Optional[str] = None

@router.get("", response_model=List[VocabularyResponse])
async def list_vocabulary(
    level: Optional[str] = Query(None, description="Filter by CEFR level (A1, A2, B1)"),
    topic: Optional[str] = Query(None, description="Filter by topic keyword"),
    status: Optional[str] = Query(None, description="Filter by status: new, learning, mastered"),
    search: Optional[str] = Query(None, description="Search term in word, translation, topic"),
    limit: int = Query(200, ge=1, le=500)
):
    """Retrieve learner vocabulary cards with search and filters."""
    return await VocabularyService.list_vocabulary(
        level=level,
        topic=topic,
        status=status,
        search=search,
        limit=limit
    )

@router.post("", response_model=VocabularyResponse, status_code=status.HTTP_201_CREATED)
async def create_vocabulary(data: VocabularyCreate):
    """Manually add a vocabulary word or phrase."""
    return await VocabularyService.create_vocabulary(data)

@router.post("/batch", status_code=status.HTTP_201_CREATED)
async def batch_create_vocabulary(data: VocabularyBatchCreate):
    """Save multiple vocabulary words from a lesson or reviewed material."""
    count = await VocabularyService.batch_create_vocabulary(data)
    return {"message": f"Successfully saved {count} vocabulary items.", "saved_count": count}

@router.patch("/{vocab_id}", response_model=VocabularyResponse)
async def update_vocabulary(vocab_id: str, data: VocabularyUpdate):
    """Update vocabulary status, mastery score, article, or meaning."""
    updated = await VocabularyService.update_vocabulary(vocab_id, data)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vocabulary item '{vocab_id}' not found"
        )
    return updated

@router.delete("/{vocab_id}")
async def delete_vocabulary(vocab_id: str):
    """Remove a vocabulary item."""
    success = await VocabularyService.delete_vocabulary(vocab_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vocabulary item '{vocab_id}' not found"
        )
    return {"message": "Vocabulary deleted successfully", "id": vocab_id}

@router.post("/extract-from-material", response_model=ExtractVocabularyResponse)
async def extract_vocabulary_from_material(req: ExtractFromMaterialRequest):
    """
    Rule-based extraction of candidate vocabulary from an uploaded material or raw text.
    Returns candidate items for learner review without fabricating translations or articles.
    """
    raw_text = req.text
    material_title = None

    if req.material_id:
        db = get_db()
        mat_query = ({"_id": ObjectId(req.material_id)} if ObjectId.is_valid(req.material_id) else {"id": req.material_id})
        mat_query["user_id"] = current_user_id()
        mat = await db.materials.find_one(mat_query)
        if mat:
            material_title = mat.get("title")
            raw_text = raw_text or mat.get("extracted_text")

    if not raw_text:
        return ExtractVocabularyResponse(items=[], total_found=0, material_id=req.material_id, material_title=material_title)

    return VocabularyService.extract_vocabulary_from_text(
        text=raw_text,
        material_id=req.material_id,
        material_title=material_title
    )
