from pydantic import BaseModel, Field, ConfigDict, model_validator, field_validator
from typing import Optional, List, Dict, Any, Union

# ==================== 1. Reading (Lesen) Models ====================

class VocabularyHint(BaseModel):
    word: str
    article: Optional[str] = None
    meaning_en: str
    part_of_speech: Optional[str] = None

class ReadingQuestion(BaseModel):
    id: str
    question: str
    type: str = "multiple_choice"  # multiple_choice, true_false, short_answer
    options: List[str] = []
    correct_answer: Any
    acceptable_alternatives: List[str] = []
    explanation_en: str

class ReadingExerciseBase(BaseModel):
    id: str
    title: str
    cefr_level: str = "A1"  # A1, A2, B1
    topic: str
    difficulty: str = "Easy"  # Easy, Moderate, Challenging
    text_type: str = "passage"  # passage, dialogue, email, notice, story, schedule
    passage_de: str
    translation_en: str
    vocabulary_hints: List[VocabularyHint] = []
    questions: List[ReadingQuestion] = []
    source_material_id: Optional[str] = None
    source_lesson_id: Optional[str] = None

class ReadingExerciseLearnerView(BaseModel):
    """Learner view: hides correct answers and full translation until submission."""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    title: str
    cefr_level: str
    topic: str
    difficulty: str
    text_type: str
    is_seeded: bool = False
    passage_de: str
    vocabulary_hints: List[VocabularyHint] = []
    questions: List[Dict[str, Any]] = []
    source_material_id: Optional[str] = None
    source_lesson_id: Optional[str] = None

class ReadingSubmissionRequest(BaseModel):
    answers: Dict[str, Any]  # {question_id: user_answer}
    time_spent_seconds: Optional[int] = Field(default=None, ge=0, le=86400)

    @field_validator("answers")
    @classmethod
    def validate_answers(cls, value):
        if len(value) > 50:
            raise ValueError("Too many answers submitted.")
        if any(not isinstance(answer, (str, int, float, bool)) for answer in value.values()):
            raise ValueError("Answers must be text or a simple choice.")
        if any(len(str(answer)) > 500 for answer in value.values()):
            raise ValueError("An answer is too long.")
        return value

class QuestionEvaluation(BaseModel):
    question_id: str
    is_correct: bool
    user_answer: Any
    correct_answer: Any
    explanation_en: str

class ReadingSubmissionResponse(BaseModel):
    exercise_id: str
    score: int
    is_perfect: bool
    results: List[QuestionEvaluation]
    translation_en: str
    feedback: str
    completed_at: str

# ==================== 2. Listening (Hören) Models ====================

class ListeningQuestion(BaseModel):
    id: str
    question: str
    type: str = "multiple_choice"  # multiple_choice, true_false, fill_blank
    options: List[str] = []
    correct_answer: Any
    acceptable_alternatives: List[str] = []
    explanation_en: str

class ListeningExerciseBase(BaseModel):
    id: str
    title: str
    cefr_level: str = "A1"
    topic: str
    difficulty: str = "Easy"
    audio_type: str = "dialogue"  # dialogue, announcement, voicemail, interview
    audio_url: Optional[str] = None  # None indicates native/browser speech synthesis
    script_de: str
    translation_en: str
    questions: List[ListeningQuestion] = []
    source_material_id: Optional[str] = None
    source_lesson_id: Optional[str] = None
    is_seeded: bool = False

class ListeningExerciseLearnerView(BaseModel):
    """Learner view: answer key and transcript text stay hidden until submission.

    audio_text is supplied only as the utterance for browser speech synthesis; the
    frontend must not render it as a transcript before the learner submits.
    """
    model_config = ConfigDict(populate_by_name=True)

    id: str
    title: str
    cefr_level: str
    topic: str
    difficulty: str
    audio_type: str
    audio_url: Optional[str] = None
    audio_text: Optional[str] = None
    questions: List[Dict[str, Any]] = []
    source_material_id: Optional[str] = None
    source_lesson_id: Optional[str] = None

class ListeningSubmissionRequest(BaseModel):
    answers: Dict[str, Any]
    time_spent_seconds: Optional[int] = None

class ListeningSubmissionResponse(BaseModel):
    exercise_id: str
    score: int
    is_perfect: bool
    results: List[QuestionEvaluation]
    script_de: str
    translation_en: str
    feedback: str
    completed_at: str

# ==================== 3. Writing (Schreiben) Models ====================

class WritingPromptBase(BaseModel):
    id: str
    title: str
    cefr_level: str = "A1"
    topic: str
    task_type: str  # sentence_construction, translation, paragraph, email, invitation, routine, experience, opinion
    instruction_en: str
    guide_points: List[str] = []
    suggested_word_count: Optional[str] = None  # e.g. "20-40 words"
    sample_solution_de: str
    sample_solution_en: Optional[str] = None
    vocabulary_help: List[Dict[str, str]] = []
    is_seeded: bool = False

class WritingDraftRequest(BaseModel):
    prompt_id: str
    content: str
    title: Optional[str] = None

class WritingDraftResponse(BaseModel):
    id: str
    prompt_id: str
    content: str
    updated_at: str

class WritingSubmissionRequest(BaseModel):
    prompt_id: str
    content: str
    cefr_level: str = "A1"
    time_spent_seconds: Optional[int] = None

class WritingEvaluationResponse(BaseModel):
    id: str
    prompt_id: str
    original_text: str
    corrected_text: str
    grammar_mistakes: List[str] = []
    word_order_mistakes: List[str] = []
    article_mistakes: List[str] = []
    spelling_mistakes: List[str] = []
    explanation_en: str
    natural_alternative_de: Optional[str] = None
    suggestions: List[str] = []
    score: Optional[int] = None  # omitted for deterministic rule-based feedback
    is_ai_evaluated: bool = True
    evaluation_source: str = "ollama"  # ollama or deterministic_rules
    timestamp: str

# ==================== 4. Speaking (Sprechen) Models ====================

class SpeakingScenario(BaseModel):
    id: str
    title: str
    cefr_level: str = "A1"
    topic: str
    activity_type: str = "role_play"  # role_play, introduction, interview, description, opinion
    role_learner: str  # e.g. "Customer ordering coffee"
    role_tutor: str    # e.g. "Café Barista"
    initial_prompt_de: str
    initial_translation_en: str
    scenario_guide: str
    suggested_phrases: List[Dict[str, str]] = []
    is_seeded: bool = False

class SpeakingSessionStartRequest(BaseModel):
    scenario_id: Optional[str] = None
    cefr_level: str = "A1"
    topic: Optional[str] = None

class SpeakingMessageRequest(BaseModel):
    message: str
    audio_url: Optional[str] = None

class SpeakingMessageResponse(BaseModel):
    session_id: str
    role: str = "assistant"
    text_de: str
    translation_en: str
    corrections: Optional[Dict[str, Any]] = None
    turn_count: int = 1
    timestamp: str

# ==================== 5. Skills Progress & Analytics ====================

class SkillMetric(BaseModel):
    completed_count: int = 0
    average_score: Optional[int] = None
    total_time_minutes: int = 0

class PracticeProgressResponse(BaseModel):
    overall_skill_scores: Dict[str, Optional[int]]
    reading: SkillMetric
    listening: SkillMetric
    writing: SkillMetric
    speaking: SkillMetric
    total_completed: int
    total_study_minutes: int
    streak_days: int
    recent_activity: List[Dict[str, Any]] = []
    cefr_breakdown: Dict[str, int] = {}
