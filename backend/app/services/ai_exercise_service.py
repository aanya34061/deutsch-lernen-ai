import json
import re
import random
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

def _clean_strings(values: Any) -> List[str]:
    if not isinstance(values, list):
        return []
    cleaned = []
    for value in values:
        if value is None or isinstance(value, (dict, list)):
            continue
        text = str(value).strip()
        if text and text not in cleaned:
            cleaned.append(text)
    return cleaned

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
            get_field = lambda key, default=None: lesson.get(key, default) if isinstance(lesson, dict) else getattr(lesson, key, default)
            level = get_field("cefr_level", level)
            topic = get_field("topic", topic)
            grammar_rules = get_field("grammar_rules", []) or []
            rule_names = [
                rule.get("name", "") if isinstance(rule, dict) else str(rule)
                for rule in grammar_rules
            ]
            examples = get_field("examples", []) or []
            example_text = [
                f"{example.get('german', '')} ({example.get('english', '')})" if isinstance(example, dict)
                else f"{getattr(example, 'german', '')} ({getattr(example, 'english', '')})"
                for example in examples[:4]
            ]
            context_text = (
                f"Lesson Title: {get_field('title', '')}\n"
                f"Level: {level}\n"
                f"Topic: {topic}\n"
                f"Explanation: {get_field('explanation_en', '')}\n"
                f"Grammar Rules: {', '.join(name for name in rule_names if name)}\n"
                f"Examples: {', '.join(text for text in example_text if text.strip(' ()'))}"
            )

        if material_id:
            mid = ObjectId(material_id) if ObjectId.is_valid(material_id) else material_id
            doc = await db.materials.find_one({**({"_id": mid} if isinstance(mid, ObjectId) else {"id": str(mid)}), "user_id": "default", "is_seeded": {"$ne": True}})
            if not doc or doc.get("status") != "ready" or not (doc.get("extracted_text") or "").strip():
                raise ValueError(f"Study material '{material_id}' was not found.")
            if not lesson_id:
                level = doc.get("cefr_level", level)
                topic = doc.get("topic", "Study Material")
            else:
                topic = f"{topic} and {doc.get('topic', 'Study Material')}"
            raw_text = doc.get("extracted_text") or doc.get("summary") or ""
            material_context = f"Study Material Title: {doc.get('title')}\nSource content (use only these facts):\n{raw_text[:12000]}"
            context_text = f"{context_text}\n\n{material_context}" if context_text else material_context
            return context_text, topic, level

        if lesson_id:
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
    async def _fallback_items(cls, lesson_id: Optional[str], level: str) -> List[Dict[str, Any]]:
        """Return authored curriculum questions when local AI output is incomplete."""
        if lesson_id:
            lesson = next((item for item in ALL_STATIC_LESSONS if item.get("id") == lesson_id), None)
            if not lesson:
                db = get_db()
                query = {"_id": ObjectId(lesson_id)} if ObjectId.is_valid(lesson_id) else {"id": lesson_id}
                lesson = await db.lessons.find_one(query)
                if lesson:
                    lesson["id"] = str(lesson.get("_id", lesson.get("id", lesson_id)))
            lessons = [lesson] if lesson else []
        else:
            lessons = [lesson for lesson in ALL_STATIC_LESSONS if lesson.get("cefr_level", "A1").upper() == level.upper()]

        items: List[Dict[str, Any]] = []
        for lesson in lessons:
            if not lesson:
                continue
            for exercise in lesson.get("exercises", []):
                if isinstance(exercise, dict):
                    item = dict(exercise)
                    item["_fallback_lesson_id"] = lesson.get("id") or lesson_id
                    item["_fallback_topic"] = lesson.get("topic")
                    items.append(item)
        return items

    @staticmethod
    def _normalize_item(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate each exercise type so the learner UI and evaluator agree."""
        ex_type = item.get("type")
        if ex_type not in VALID_EXERCISE_TYPES:
            return None

        question = str(item.get("question") or "").strip()
        if not question:
            return None
        prompt = item.get("prompt")
        prompt = str(prompt).strip() if prompt is not None else None
        explanation = str(item.get("explanation_en") or "Review the lesson grammar rules.").strip()
        correct_sentence = item.get("correct_sentence_de")
        correct_sentence = str(correct_sentence).strip() if correct_sentence else None
        alternatives = _clean_strings(item.get("acceptable_alternatives"))
        options = _clean_strings(item.get("options"))
        correct_answer = item.get("correct_answer")
        matching_pairs: List[Dict[str, str]] = []

        if ex_type == "multiple_choice":
            if correct_answer is None or isinstance(correct_answer, (dict, list)):
                return None
            correct_answer = str(correct_answer).strip()
            if not correct_answer:
                return None
            options = [option for option in options if option != correct_answer]
            options = [correct_answer, *options[:3]]
            if len(options) < 2:
                return None
            random.shuffle(options)
        elif ex_type == "true_false":
            answer = str(correct_answer).strip().lower()
            if answer in {"true", "t", "yes", "ja", "richtig", "1"}:
                correct_answer = "True"
            elif answer in {"false", "f", "no", "nein", "falsch", "0"}:
                correct_answer = "False"
            else:
                return None
            options = ["True", "False"]
        elif ex_type == "sentence_order":
            if correct_answer is None or isinstance(correct_answer, (dict, list)):
                return None
            correct_answer = " ".join(str(correct_answer).split())
            if not correct_answer:
                return None
            expected_tokens = correct_answer.split()
            if sorted(options) != sorted(expected_tokens):
                options = expected_tokens[:]
            random.shuffle(options)
            if len(options) > 1 and options == expected_tokens:
                options = options[1:] + options[:1]
        elif ex_type in {"fill_blank", "translate"}:
            if correct_answer is None or isinstance(correct_answer, (dict, list)):
                return None
            correct_answer = str(correct_answer).strip()
            if not correct_answer:
                return None
            if not prompt:
                prompt = question
        elif ex_type == "matching":
            source_pairs = item.get("matching_pairs")
            if not isinstance(source_pairs, list):
                return None
            seen_german = set()
            seen_english = set()
            for pair in source_pairs:
                if not isinstance(pair, dict):
                    continue
                german = str(pair.get("german") or "").strip()
                english = str(pair.get("english") or "").strip()
                if german and english and german not in seen_german and english not in seen_english:
                    matching_pairs.append({"german": german, "english": english})
                    seen_german.add(german)
                    seen_english.add(english)
            if len(matching_pairs) < 2:
                return None
            correct_answer = {pair["german"]: pair["english"] for pair in matching_pairs}

        return {
            "type": ex_type,
            "question": question,
            "prompt": prompt,
            "options": options,
            "matching_pairs": matching_pairs,
            "correct_answer": correct_answer,
            "acceptable_alternatives": alternatives,
            "explanation_en": explanation,
            "correct_sentence_de": correct_sentence,
        }

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
            "When a Study Material is provided, every question and answer must be directly supported by that source. "
            "Do not introduce outside topics, unstated grammar rules, or made-up source details. Omit a question if unsure.\n"
            "Output ONLY a valid JSON array of objects. Do not wrap in commentary or markdown conversational text.\n"
            "Each question object must strictly adhere to this schema:\n"
            "[\n"
            "  {\n"
            "    \"type\": \"multiple_choice\" | \"fill_blank\" | \"translate\" | \"sentence_order\" | \"true_false\" | \"matching\",\n"
            "    \"question\": \"Question text in German or English\",\n"
            "    \"prompt\": \"Helpful instruction for the learner\",\n"
            "    \"options\": [\"opt1\", \"opt2\", \"opt3\"],\n"
            "    \"matching_pairs\": [{\"german\": \"Guten Morgen\", \"english\": \"Good morning\"}],\n"
            "    \"correct_answer\": \"exact answer string; German-to-English object for matching\",\n"
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

        if not isinstance(raw_exercises, list):
            raw_exercises = []

        # Preserve strict grounding for uploaded notes. Authored curriculum
        # questions safely fill gaps when local AI output is malformed.
        fallback_items = [] if material_id else await cls._fallback_items(lesson_id, level)
        candidates = [item for item in raw_exercises if isinstance(item, dict)]
        seen_questions = {str(item.get("question", "")).strip().casefold() for item in candidates}
        for item in fallback_items:
            key = str(item.get("question", "")).strip().casefold()
            if key and key not in seen_questions:
                candidates.append(item)
                seen_questions.add(key)

        if not candidates:
            if material_id:
                raise RuntimeError("The model did not return valid questions supported by this source material.")
            raise RuntimeError("No valid practice questions are available for this level yet.")

        # Validate and prepare documents for persistence
        validated_docs = []
        learner_views = []
        db = get_db()

        for item in candidates:
            normalized = cls._normalize_item(item)
            if not normalized:
                continue

            ex_type = normalized["type"]
            question = normalized["question"]
            prompt = normalized["prompt"]
            correct_answer = normalized["correct_answer"]
            options = normalized["options"]
            explanation = normalized["explanation_en"]
            correct_sentence = normalized["correct_sentence_de"]
            alternatives = normalized["acceptable_alternatives"]
            matching_pairs = normalized["matching_pairs"]

            unique_id = f"ai_{uuid.uuid4().hex[:12]}"
            doc = {
                "id": unique_id,
                "lesson_id": lesson_id or item.get("_fallback_lesson_id"),
                "material_id": material_id,
                "cefr_level": level,
                "topic": item.get("_fallback_topic") or topic,
                "type": ex_type,
                "skill": "grammar",
                "question": question,
                "prompt": prompt,
                "options": options,
                "matching_pairs": matching_pairs,
                "correct_answer": correct_answer,
                "acceptable_alternatives": alternatives,
                "explanation_en": explanation,
                "correct_sentence_de": correct_sentence,
                "difficulty": "beginner" if level == "A1" else ("intermediate" if level == "A2" else "advanced"),
                "is_ai_generated": not bool(item.get("_fallback_lesson_id")),
                "is_seeded": False
            }
            if material_id:
                material = await db.materials.find_one({"_id": ObjectId(material_id), "user_id": "default", "is_seeded": {"$ne": True}}) if ObjectId.is_valid(material_id) else None
                doc.update({"user_id": "default", "origin": "tutor_generated", "source_type": "uploaded_material", "source_title": material.get("title") if material else None})

            validated_docs.append(doc)
            learner_views.append(
                ExerciseLearnerView(
                    id=unique_id,
                    lesson_id=doc["lesson_id"],
                    cefr_level=level,
                    topic=doc["topic"],
                    type=ex_type,
                    skill="grammar",
                    question=question,
                    prompt=prompt,
                    options=options,
                    matching_pairs=matching_pairs,
                    difficulty=doc["difficulty"]
                )
            )
            if len(validated_docs) >= target_count:
                break

        # Persist generated exercises into MongoDB exercises collection
        if material_id and len(validated_docs) < target_count:
            raise RuntimeError("The model did not return enough valid questions supported by this source material. Try again or select a different note.")
        if validated_docs:
            try:
                await db.exercises.insert_many(validated_docs)
                logger.info(f"Persisted {len(validated_docs)} AI-generated exercises to database.")
            except Exception as db_err:
                logger.exception("Could not persist generated exercises")
                raise RuntimeError("Generated exercises could not be saved. Please try again.") from db_err

        return learner_views
