from pydantic import BaseModel, Field, ConfigDict, model_validator, computed_field
from typing import Optional, List, Any

class VocabularyBase(BaseModel):
    word: str
    article: Optional[str] = ""  # der, die, das, or empty
    plural: Optional[str] = ""   # e.g., die Äpfel or -n, -er
    meaning_en: str
    example_de: Optional[str] = None
    example_en: Optional[str] = None
    cefr_level: str = "A1"
    topic: str = "General"
    status: str = "new"  # new, learning, mastered
    source_type: str = "manual"  # manual, lesson, upload
    source_id: Optional[str] = None
    source_title: Optional[str] = None
    mastery_score: int = 20  # 0 to 100
    due_for_revision: bool = True
    mistakes_count: int = 0
    notes: Optional[str] = None

class VocabularyCreate(VocabularyBase):
    user_id: Optional[str] = None

class VocabularyBatchCreate(BaseModel):
    words: List[VocabularyBase]
    source_type: str = "lesson"
    source_id: Optional[str] = None
    source_title: Optional[str] = None

class VocabularyUpdate(BaseModel):
    word: Optional[str] = None
    article: Optional[str] = None
    plural: Optional[str] = None
    meaning_en: Optional[str] = None
    example_de: Optional[str] = None
    example_en: Optional[str] = None
    cefr_level: Optional[str] = None
    topic: Optional[str] = None
    status: Optional[str] = None  # new, learning, mastered
    mastery_score: Optional[int] = None
    due_for_revision: Optional[bool] = None
    notes: Optional[str] = None

class VocabularyResponse(VocabularyBase):
    model_config = ConfigDict(populate_by_name=True)

    id: str = ""
    user_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def populate_id(cls, data: Any) -> Any:
        if isinstance(data, dict):
            val = data.get("id") or data.get("_id")
            if val is not None:
                data["id"] = str(val)
        return data

    @computed_field
    @property
    def _id(self) -> str:
        return self.id

class ExtractedVocabularyItem(BaseModel):
    word: str
    article: Optional[str] = ""
    plural: Optional[str] = ""
    meaning_en: str
    example_context: Optional[str] = None
    cefr_level: str = "A1"
    topic: str = "General"
    confidence: str = "high"  # high, needs_review
    is_uncertain: bool = False
    review_note: Optional[str] = None

class ExtractVocabularyResponse(BaseModel):
    items: List[ExtractedVocabularyItem]
    total_found: int
    material_id: Optional[str] = None
    material_title: Optional[str] = None
