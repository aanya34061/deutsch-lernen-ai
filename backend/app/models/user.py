from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str
    name: str = "German Learner"
    current_level: str = "A1"
    target_level: str = "B1"
    native_language: str = "English"
    daily_goal_minutes: int = 20
    streak_days: int = 0

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    name: Optional[str] = None
    current_level: Optional[str] = None
    target_level: Optional[str] = None
    native_language: Optional[str] = None
    daily_goal_minutes: Optional[int] = None

class UserResponse(UserBase):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id", default="")
    created_at: Optional[str] = None
