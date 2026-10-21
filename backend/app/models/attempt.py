from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any

class AttemptCreate(BaseModel):
    exercise_id: str
    user_id: Optional[str] = None
    skill: str
    user_response: str
    score: int  # 0 to 100
    feedback: Optional[str] = None
    corrections: Optional[Dict[str, Any]] = None

class AttemptResponse(AttemptCreate):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id", default="")
    timestamp: Optional[str] = None
