import json
import re
import uuid
import logging
from typing import List, Dict, Any, Optional
from bson import ObjectId

from app.config import settings
from app.database import get_db
from app.models.exercise import ExerciseLearnerView
from app.services.ollama_service import OllamaService
from app.services.curriculum_service import CurriculumService, ALL_STATIC_LESSONS

logger = logging.getLogger("german_app.ai_exercises")

VALID_EXERCISE_TYPES = [
    "multiple_choice",
    "fill_blank",
    "translate",
    "sentence_order",
    "true_false",
    "matching"
]

class AiExerciseService:
    @staticmethod
    def _extract_json_from_response(text: str) -> Optional[List[Dict[str, Any]]]:
        """Robustly extract JSON array from LLM response text."""
        cleaned = text.strip()
        # Strip markdown fences if present
        fence_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', cleaned)
        if fence_match:
            cleaned = fence_match.group(1).strip()

        # Find first '[' and last ']'
        start = cleaned.find('[')
        end = cleaned.rfind(']')
        if start != -1 and end != -1 and end > start:
            json_substr = cleaned[start:end+1]
            try:
                parsed = json.loads(json_substr)
                if isinstance(parsed, list):
                    return parsed
            except Exception as e:
                logger.debug(f"JSON array parsing failed: {e}")

        # Try parsing whole text
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict) and "exercises" in parsed and isinstance(parsed["exercises"], list):
                return parsed["exercises"]
        except Exception:
            pass

        return None

    @classmethod
    async def _get_source_context(
        cls,
        lesson_id: Optional[str] = None,
        material_id: Optional[str] = None,
        cefr_level: str = "A1"
    ) -> tuple[str, str, str]:
        """Fetch reference text and determine topic/level."""
        db = get_db()
        level = cefr_level.upper() if cefr_level else "A1"
        topic = "General German Grammar"
        context_text = ""

        if lesson_id:
            lesson = await CurriculumService.get_lesson(lesson_id)
            if not lesson:
                raise ValueError(f"Lesson '{lesson_id}' was not found.")
            level = lesson.cefr_level
            topic = lesson.topic
            context_text = (
                f"Lesson Title: {lesson.title}\n"
                f"Level: {lesson.cefr_level}\n"
                f"Topic: {lesson.topic}\n"
                f"Explanation: {lesson.explanation_en}\n"
                f"Grammar Rules: {', '.join(lesson.grammar_rules)}\n"
                f"Examples: {', '.join([f'{ex.german} ({ex.english})' for ex in lesson.examples[:4]])}"
            )
            return context_text, topic, level

        if material_id:
            mid = ObjectId(material_id) if ObjectId.is_valid(material_id) else material_id
            doc = await db.materials.find_one({"_id": mid} if isinstance(mid, ObjectId) else {"id": str(mid)})
            if not doc or doc.get("is_seeded") is True:
                raise ValueError(f"Study material '{material_id}' was not found.")
            level = doc.get("cefr_level", level)
            topic = doc.get("topic", "Study Material")
            raw_text = doc.get("extracted_text") or doc.get("summary") or ""
            context_text = f"Study Material Title: {doc.get('title')}\nContent Snippet:\n{raw_text[:1200]}"
            return context_text, topic, level

        # Fallback to static curriculum context for requested level
        matching_lesson = next((l for l in ALL_STATIC_LESSONS if l.get("cefr_level") == level), ALL_STATIC_LESSONS[0])
        topic = matching_lesson.get("topic", "German Basics")
        context_text = (
            f"Level: {level}\n"
            f"Topic: {topic}\n"
            f"Summary: {matching_lesson.get('summary', '')}"
        )
        return context_text, topic, level

    @classmethod
    async def generate_exercises(
        cls,
        lesson_id: Optional[str] = None,
        material_id: Optional[str] = None,
        cefr_level: str = "A1",
        count: int = 3,
        exercise_types: Optional[List[str]] = None
    ) -> List[ExerciseLearnerView]:
        """
        Generate structured, validated German practice exercises based on a lesson or study material.
        Persists exercises in MongoDB exercises collection and returns learner views ready for ExerciseRunner.
        """
        target_count = max(1, min(5, count))
        context_text, topic, level = await cls._get_source_context(lesson_id, material_id, cefr_level)

        prompt_system = (
            "You are an expert German language test author. Generate high-quality practice questions for German learners.\n"
            "Output ONLY a valid JSON array of objects. Do not wrap in commentary or markdown conversational text.\n"
            "Each question object must strictly adhere to this schema:\n"
            "[\n"
            "  {\n"
            "    \"type\": \"multiple_choice\" | \"fill_blank\" | \"translate\" | \"sentence_order\" | \"true_false\",\n"
            "    \"question\": \"Question text in German or English\",\n"
            "    \"prompt\": \"Helpful instruction for the learner\",\n"
            "    \"options\": [\"opt1\", \"opt2\", \"opt3\"], // For multiple_choice, true_false, sentence_order chips\n"
            "    \"correct_answer\": \"exact correct answer string\",\n"
            "    \"acceptable_alternatives\": [\"alt1\"],\n"
            "    \"explanation_en\": \"Clear grammatical explanation in English why this is correct\",\n"
            "    \"correct_sentence_de\": \"Complete correct German sentence\"\n"
            "  }\n"
            "]"
        )

        user_prompt = (
            f"Generate exactly {target_count} practice exercises appropriate for CEFR {level}.\n"
            f"Topic: {topic}\n"
            f"Reference Material:\n{context_text}\n\n"
            "Ensure questions are pedagogical, accurate, beginner-friendly, and include clear English explanations."
        )

        raw_exercises = None
        try:
            # Check Ollama status
            status = await OllamaService.check_status()
            if status["is_ready"]:
                response_str = await OllamaService.generate_chat(
                    messages=[{"role": "user", "content": user_prompt}],
                    system_prompt=prompt_system,
                    temperature=0.2
                )
                raw_exercises = cls._extract_json_from_response(response_str)
        except Exception as e:
            logger.warning(f"AI exercise generation failed: {e}")

        if not raw_exercises or not isinstance(raw_exercises, list) or len(raw_exercises) == 0:
            raise RuntimeError("Local AI exercise generation is unavailable or returned no valid exercises.")

        # Validate and prepare documents for persistence
        validated_docs = []
        learner_views = []
        db = get_db()

        for idx, item in enumerate(raw_exercises[:target_count]):
            if not isinstance(item, dict):
                continue

            ex_type = item.get("type", "multiple_choice")
            if ex_type not in VALID_EXERCISE_TYPES:
                ex_type = "multiple_choice"

            question = str(item.get("question") or f"Question {idx+1}").strip()
            prompt = item.get("prompt")
            correct_answer = item.get("correct_answer")
            options = item.get("options") or []
            explanation = item.get("explanation_en") or "Review the lesson grammar rules."
            correct_sentence = item.get("correct_sentence_de")
            alternatives = item.get("acceptable_alternatives") or []

            # Specific fixes per type
            if ex_type == "multiple_choice" and not options:
                options = ["der", "die", "das"] if "artikel" in question.lower() else ["Ja", "Nein", "Vielleicht"]
            if ex_type == "true_false" and not options:
                options = ["True", "False"]
            if ex_type == "sentence_order":
                if not options and correct_answer:
                    # Create shuffled tokens from correct answer
                    options = [w for w in re.split(r'\s+', str(correct_answer)) if w]
                    import random
                    random.shuffle(options)

            if not correct_answer:
                correct_answer = options[0] if options else "richtig"

            unique_id = f"ai_{uuid.uuid4().hex[:12]}"
            doc = {
                "id": unique_id,
                "lesson_id": lesson_id,
                "material_id": material_id,
                "cefr_level": level,
                "topic": topic,
                "type": ex_type,
                "skill": "grammar",
                "question": question,
                "prompt": prompt,
                "options": options,
                "matching_pairs": item.get("matching_pairs", []),
                "correct_answer": correct_answer,
                "acceptable_alternatives": alternatives,
                "explanation_en": explanation,
                "correct_sentence_de": correct_sentence,
                "difficulty": "beginner" if level == "A1" else ("intermediate" if level == "A2" else "advanced"),
                "is_ai_generated": True
            }

            validated_docs.append(doc)
            learner_views.append(
                ExerciseLearnerView(
                    id=unique_id,
                    lesson_id=lesson_id,
                    cefr_level=level,
                    topic=topic,
                    type=ex_type,
                    skill="grammar",
                    question=question,
                    prompt=prompt,
                    options=options,
                    matching_pairs=item.get("matching_pairs", []),
                    difficulty=doc["difficulty"]
                )
            )

        # Persist generated exercises into MongoDB exercises collection
        if validated_docs:
            try:
                await db.exercises.insert_many(validated_docs)
                logger.info(f"Persisted {len(validated_docs)} AI-generated exercises to database.")
            except Exception as db_err:
                logger.exception("Could not persist generated exercises")
                raise RuntimeError("Generated exercises could not be saved. Please try again.") from db_err

        return learner_views
