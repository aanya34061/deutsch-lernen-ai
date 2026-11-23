import re
import logging
from typing import Optional, Any, Dict, List
from datetime import datetime, timezone
from app.models.exercise import (
    ExerciseBase,
    ExerciseLearnerView,
    ExerciseSubmissionResponse
)
from app.services.curriculum_service import CurriculumService, ALL_STATIC_LESSONS
from app.database import get_db

logger = logging.getLogger("german_app.exercises")

class ExerciseService:
    @staticmethod
    def _normalize_string(text: str) -> str:
        """Removes punctuation and normalizes spaces for lenient comparison."""
        cleaned = re.sub(r'[.,!?;:"\']', '', text)
        return " ".join(cleaned.strip().lower().split())

    @staticmethod
    async def get_exercise_by_id(exercise_id: str) -> Optional[Dict[str, Any]]:
        """Finds exercise definition across all lessons (static and custom in DB)."""
        db = get_db()
        # Prefer persisted curriculum content so safe manifest updates and edits
        # are the same source used by lesson detail and answer evaluation.
        curriculum_collection = getattr(db, "curriculum_lessons", None)
        curriculum_doc = await curriculum_collection.find_one({"exercises.id": exercise_id}) if curriculum_collection is not None else None
        if curriculum_doc:
            for ex in curriculum_doc.get("exercises", []):
                if ex.get("id") == exercise_id:
                    return ex

        # 1. Search in static curriculum
        for lesson in ALL_STATIC_LESSONS:
            for ex in lesson.get("exercises", []):
                if ex.get("id") == exercise_id:
                    return ex

        # 2. Search in MongoDB lessons
        doc = await db.lessons.find_one({"exercises.id": exercise_id})
        if doc:
            for ex in doc.get("exercises", []):
                if ex.get("id") == exercise_id:
                    return ex

        # Search standalone database exercises (including AI generated ones).
        from bson import ObjectId
        standalone_ex = await db.exercises.find_one({"id": exercise_id})
        if not standalone_ex and ObjectId.is_valid(exercise_id):
            standalone_ex = await db.exercises.find_one({"_id": ObjectId(exercise_id)})
        if standalone_ex:
            if "_id" in standalone_ex:
                standalone_ex["id"] = standalone_ex.get("id") or str(standalone_ex["_id"])
            return standalone_ex

        return None

    @staticmethod
    async def get_learner_view(exercise_id: str) -> Optional[ExerciseLearnerView]:
        """Returns exercise view for learner without revealing correct answer."""
        ex = await ExerciseService.get_exercise_by_id(exercise_id)
        if not ex:
            return None
        return ExerciseLearnerView(
            id=ex.get("id", exercise_id),
            lesson_id=ex.get("lesson_id"),
            cefr_level=ex.get("cefr_level", "A1"),
            topic=ex.get("topic", "General"),
            type=ex.get("type", "multiple_choice"),
            skill=ex.get("skill", "grammar"),
            question=ex.get("question", ""),
            prompt=ex.get("prompt"),
            options=ex.get("options", []),
            matching_pairs=ex.get("matching_pairs", []),
            difficulty=ex.get("difficulty", "beginner")
        )

    @staticmethod
    async def evaluate_submission(
        exercise_id: str,
        user_answer: Any
    ) -> ExerciseSubmissionResponse:
        """Evaluates learner submission across all 6 question types and records attempt."""
        ex = await ExerciseService.get_exercise_by_id(exercise_id)
        if not ex:
            raise ValueError(f"Exercise '{exercise_id}' not found")

        ex_type = ex.get("type", "multiple_choice")
        correct_answer = ex.get("correct_answer")
        alternatives = ex.get("acceptable_alternatives", [])
        explanation = ex.get("explanation_en") or "Review the grammar rules and lesson examples."
        correct_sentence = ex.get("correct_sentence_de")

        is_correct = False

        if ex_type == "multiple_choice" or ex_type == "true_false":
            # Direct string comparison (case-insensitive)
            user_str = str(user_answer).strip().lower()
            correct_str = str(correct_answer).strip().lower()
            is_correct = user_str == correct_str

        elif ex_type == "fill_blank" or ex_type == "translate":
            user_norm = ExerciseService._normalize_string(str(user_answer))
            correct_norm = ExerciseService._normalize_string(str(correct_answer))

            if user_norm == correct_norm:
                is_correct = True
            else:
                # Check acceptable alternatives
                for alt in alternatives:
                    if user_norm == ExerciseService._normalize_string(alt):
                        is_correct = True
                        break

        elif ex_type == "sentence_order":
            # User answer might be list of strings or single string
            if isinstance(user_answer, list):
                user_joined = " ".join(user_answer)
            else:
                user_joined = str(user_answer)

            user_norm = ExerciseService._normalize_string(user_joined)
            correct_norm = ExerciseService._normalize_string(str(correct_answer))

            if user_norm == correct_norm:
                is_correct = True
            else:
                for alt in alternatives:
                    if user_norm == ExerciseService._normalize_string(alt):
                        is_correct = True
                        break

        elif ex_type == "matching":
            # User answer is a dict mapping german -> english
            if isinstance(user_answer, dict) and isinstance(correct_answer, dict):
                is_correct = set(user_answer.keys()) == set(correct_answer.keys())
                for de_key, en_val in correct_answer.items():
                    u_val = user_answer.get(de_key)
                    if u_val is None or ExerciseService._normalize_string(str(u_val)) != ExerciseService._normalize_string(str(en_val)):
                        is_correct = False
                        break
            else:
                is_correct = False

        # Feedback message
        if is_correct:
            feedback = "Richtig! Ausgezeichnet! (Correct! Well done!)"
            score = 100
        else:
            feedback = "Leider nicht ganz richtig. (Not quite right.) Check the explanation and correct answer."
            score = 0

        # Record attempt in MongoDB
        db = get_db()
        attempt_doc = {
            "exercise_id": exercise_id,
            "user_id": "default",
            "is_seeded": False,
            "type": ex_type,
            "skill": ex.get("skill", "grammar"),
            "cefr_level": ex.get("cefr_level"),
            "user_answer": user_answer,
            "is_correct": is_correct,
            "score": score,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        try:
            await db.exercise_attempts.insert_one(attempt_doc)
        except Exception as e:
            logger.exception("Could not record exercise attempt")
            raise RuntimeError("Could not save this attempt. Please try again.") from e

        return ExerciseSubmissionResponse(
            exercise_id=exercise_id,
            is_correct=is_correct,
            score=score,
            user_answer=user_answer,
            correct_answer=correct_answer,
            explanation_en=explanation,
            correct_sentence_de=correct_sentence,
            feedback=feedback
        )
