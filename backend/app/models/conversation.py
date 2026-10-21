from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any

class MessageItem(BaseModel):
    role: str  # user, assistant, system
    content: str
    audio_url: Optional[str] = None
    corrections: Optional[Dict[str, Any]] = None
    sources: Optional[List[Dict[str, Any]]] = None
    is_rag: Optional[bool] = False
    timestamp: Optional[str] = None

class ConversationBase(BaseModel):
    user_id: Optional[str] = None
    title: Optional[str] = "German Tutor Conversation"
    cefr_level: str = "A1"
    topic: str = "General Practice"
    messages: List[MessageItem] = []

class ConversationResponse(ConversationBase):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id", default="")
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class ConversationSummary(BaseModel):
    id: str
    title: str
    cefr_level: str
    message_count: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
