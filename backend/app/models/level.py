from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

class GrammarConcept(BaseModel):
    name: str
    explanation: str

class LessonOutline(BaseModel):
    order: int
    title: str
    topic: str
    grammar: List[str]

class LevelDetail(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code: str  # A1, A2, B1, B2, C1, C2
    name: str
    description: str
    status: str  # "active", "planned"
    is_available: bool = True
    core_topics: List[str] = []
    grammar_concepts: List[GrammarConcept] = []
    lesson_outlines: List[LessonOutline] = []

class LevelSummaryResponse(BaseModel):
    levels: List[LevelDetail]
    active_level: str
    total_levels: int
