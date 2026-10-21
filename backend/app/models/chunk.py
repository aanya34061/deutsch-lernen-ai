from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List

class ChunkBase(BaseModel):
    material_id: str
    text: str
    chunk_index: int = 0
    filename: Optional[str] = None
    page_number: Optional[int] = None
    cefr_level: str = "A1"
    topic: str = "General"
    content_hash: Optional[str] = None
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = {}

class ChunkResponse(ChunkBase):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id", default="")
    created_at: Optional[str] = None
