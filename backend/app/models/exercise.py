from pydantic import BaseModel, Field, ConfigDict, model_validator, computed_field
from typing import Optional, List, Dict, Any, Union

class ExerciseBase(BaseModel):
    lesson_id: Optional[str] = None
    cefr_level: str = "A1"
    topic: str = "General"
    type: str  # multiple_choice, fill_blank, translate, sentence_order, matching, true_false
    skill: str = "grammar"  # reading, listening, writing, speaking, grammar, vocabulary
    question: str
    prompt: Optional[str] = None
    options: List[str] = []
    matching_pairs: List[Dict[str, str]] = []  # [{"german": "der Hund", "english": "the dog"}]
    correct_answer: Any = None
    acceptable_alternatives: List[str] = []
    explanation_en: Optional[str] = None
    correct_sentence_de: Optional[str] = None
    difficulty: str = "beginner"  # beginner, intermediate, advanced

class ExerciseCreate(ExerciseBase):
    pass

class ExerciseLearnerView(BaseModel):
    """Public view for learners that does NOT reveal the correct answer beforehand."""
    model_config = ConfigDict(populate_by_name=True)

    id: str = ""
    lesson_id: Optional[str] = None
    cefr_level: str = "A1"
    topic: str = "General"
    type: str
    skill: str = "grammar"
    question: str
    prompt: Optional[str] = None
    options: List[str] = []
    matching_pairs: List[Dict[str, str]] = []  # In matching, client receives items scrambled
    difficulty: str = "beginner"

    @model_validator(mode="before")
    @classmethod
    def populate_id(cls, data: Any) -> Any:
        if isinstance(data, dict):
            val = data.get("id") or data.get("_id")
            if val is not None:
                data["id"] = str(val)
        return data

class ExerciseSubmissionRequest(BaseModel):
    user_answer: Any

class ExerciseSubmissionResponse(BaseModel):
    exercise_id: str
    is_correct: bool
    score: int  # 0 to 100
    user_answer: Any
    correct_answer: Any
    explanation_en: str
    correct_sentence_de: Optional[str] = None
    feedback: str
