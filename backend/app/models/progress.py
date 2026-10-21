from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.models.vocabulary import VocabularyResponse
from app.models.material import MaterialResponse

class WeakTopic(BaseModel):
    topic: str
    skill: str
    accuracy: int

class SkillScores(BaseModel):
    reading: Optional[int] = None
    listening: Optional[int] = None
    writing: Optional[int] = None
    speaking: Optional[int] = None

class DailyStats(BaseModel):
    streak_days: int = 0
    today_minutes: int = 0
    goal_minutes: Optional[int] = None
    completed_today: int = 0
    total_exercises: int = 0

class LevelProgress(BaseModel):
    completed: int = 0
    total: int = 0

class DashboardSummaryResponse(BaseModel):
    learner_name: str
    current_level: str
    target_level: str
    daily_stats: DailyStats
    skill_scores: SkillScores
    recent_materials: List[MaterialResponse] = []
    weak_topics: List[WeakTopic] = []
    vocab_due_count: int = 0
    vocab_saved_count: int = 0
    vocab_mastered_count: int = 0
    completed_lessons_count: int = 0
    level_progress: Dict[str, LevelProgress] = Field(default_factory=dict)
    speaking_sessions_count: int = 0
    listening_resources_completed: int = 0
    vocab_queue: List[VocabularyResponse] = []

class LevelChangeRequest(BaseModel):
    cefr_level: str  # A1, A2, B1, B2, C1, C2
