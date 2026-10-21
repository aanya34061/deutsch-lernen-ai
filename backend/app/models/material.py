from pydantic import BaseModel, Field, ConfigDict, model_validator, computed_field
from typing import Optional, List, Any

# Supported material classifications
SUPPORTED_CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]
SUPPORTED_TOPICS = ["Grammar", "Vocabulary", "Lesen", "Hören", "Schreiben", "Sprechen", "General"]
SUPPORTED_FILE_TYPES = ["pdf", "docx", "txt", "image", "youtube", "link", "audio"]
SUPPORTED_STATUSES = ["uploaded", "processing", "ready", "failed"]
SUPPORTED_INDEXING_STATUSES = ["not_indexed", "indexing", "indexed", "failed"]

class MaterialBase(BaseModel):
    title: str
    file_type: str = "pdf"  # pdf, docx, txt, image, audio, youtube, link
    source_type: str = "upload"  # upload, link
    source_url: Optional[str] = None
    cefr_level: str = "A1"
    topic: str = "General"
    status: str = "ready"  # uploaded, processing, ready, failed
    error_message: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    extracted_text: Optional[str] = None
    original_filename: Optional[str] = None
    storage_filename: Optional[str] = None
    file_size: Optional[int] = None
    content_type: Optional[str] = None
    chunks_count: int = 0
    tags: List[str] = []
    # RAG Indexing fields
    indexing_status: str = "not_indexed"  # not_indexed, indexing, indexed, failed
    indexing_error: Optional[str] = None
    content_hash: Optional[str] = None
    indexed_at: Optional[str] = None

class MaterialCreate(MaterialBase):
    pass

class MaterialUpdate(BaseModel):
    title: Optional[str] = None
    cefr_level: Optional[str] = None
    topic: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None

class LearningLinkCreate(BaseModel):
    url: str
    title: Optional[str] = None
    cefr_level: str = "A1"
    topic: str = "General"
    description: Optional[str] = None

class MaterialResponse(MaterialBase):
    model_config = ConfigDict(populate_by_name=True)

    id: str = ""
    user_id: Optional[str] = None
    file_path: Optional[str] = None
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

class MaterialListResponse(BaseModel):
    items: List[MaterialResponse]
    total: int
    page: int = 1
    limit: int = 100
