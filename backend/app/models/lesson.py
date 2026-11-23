from pydantic import BaseModel, Field, ConfigDict, model_validator, computed_field
from typing import Optional, List, Dict, Any

class GrammarRule(BaseModel):
    name: str
    explanation: str
    pattern: Optional[str] = None
    table: Optional[List[Dict[str, str]]] = None  # e.g., [{"pronoun": "ich", "verb": "komme"}]

class SentenceExample(BaseModel):
    german: str
    english: str
    notes: Optional[str] = None

class DialogueLine(SentenceExample):
    speaker: Optional[str] = None

class VocabularySnippet(BaseModel):
    word: str
    article: Optional[str] = ""  # der, die, das, or empty
    plural: Optional[str] = ""
    meaning_en: str
    example_de: Optional[str] = None
    example_en: Optional[str] = None

class CommonMistake(BaseModel):
    wrong: str
    correct: str
    explanation: str

class LessonBase(BaseModel):
    title: str
    cefr_level: str = "A1"  # A1, A2, B1
    module_title: str
    topic: str
    order: int = 1
    estimated_minutes: int = 15
    objectives: List[str] = []
    introduction_en: Optional[str] = None
    explanation_en: str
    sentence_patterns: List[str] = []
    grammar_rules: List[GrammarRule] = []
    examples: List[SentenceExample] = []
    practical_dialogue: List[DialogueLine] = []
    vocabulary: List[VocabularySnippet] = []
    common_mistakes: List[CommonMistake] = []
    important_notes: List[str] = []
    summary_en: str
    publication_status: str = "draft"
    module_id: Optional[str] = None
    topic_id: Optional[str] = None
    source_material_id: Optional[str] = None
    source_material_title: Optional[str] = None
    source_text: Optional[str] = None
    is_completed: bool = False
    exercises_count: int = 0

class LessonCreate(LessonBase):
    pass

class LessonCreateFromMaterial(BaseModel):
    material_id: str
    title: Optional[str] = None
    cefr_level: Optional[str] = None
    topic: Optional[str] = None
    module_title: Optional[str] = "Uploaded Study Materials"

class LessonSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = ""
    title: str
    cefr_level: str
    module_title: str
    module_id: Optional[str] = None
    topic_id: Optional[str] = None
    topic: str
    order: int
    estimated_minutes: int = 15
    objectives: List[str] = []
    is_completed: bool = False
    exercises_count: int = 0
    source_material_id: Optional[str] = None
    publication_status: str = "published"

    @model_validator(mode="before")
    @classmethod
    def populate_id(cls, data: Any) -> Any:
        if isinstance(data, dict):
            val = data.get("id") or data.get("_id")
            if val is not None:
                data["id"] = str(val)
        return data

class LessonResponse(LessonBase):
    model_config = ConfigDict(populate_by_name=True)

    id: str = ""
    exercises: List[Dict[str, Any]] = []
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
