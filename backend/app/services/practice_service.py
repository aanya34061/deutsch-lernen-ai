import re
import json
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from bson import ObjectId

from app.database import get_db
from app.models.practice import (
    ReadingExerciseBase,
    ReadingExerciseLearnerView,
    ReadingSubmissionResponse,
    QuestionEvaluation,
    ListeningExerciseBase,
    ListeningExerciseLearnerView,
    ListeningSubmissionResponse,
    WritingPromptBase,
    WritingDraftResponse,
    WritingEvaluationResponse,
    SpeakingScenario,
    SpeakingMessageResponse,
    PracticeProgressResponse,
    SkillMetric
)
from app.services.ollama_service import OllamaService
from app.data.practice_reading_data import STARTING_READING_EXERCISES
from app.data.practice_speaking_data import STARTING_SPEAKING_SCENARIOS
from app.data.listening_resources import LISTENING_RESOURCE_CATALOG

logger = logging.getLogger("german_app.practice")

def _normalize(text: str) -> str:
    """Strip punctuation and normalize whitespace for lenient answer matching."""
    cleaned = re.sub(r'[.,!?;:"\'„“]', '', str(text))
    return " ".join(cleaned.strip().lower().split())

class PracticeService:
    # ==================== 1. Reading (Lesen) ====================

    @classmethod
    async def list_reading_exercises(
        cls,
        cefr_level: Optional[str] = None,
        topic: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Query reading passages with optional level and topic filters."""
        db = get_db()
        query: Dict[str, Any] = {}
        if cefr_level and cefr_level.strip():
            query["cefr_level"] = cefr_level.strip().upper()
        if topic and topic.strip():
            query["topic"] = {"$regex": f"^{re.escape(topic.strip())}$", "$options": "i"}

        cursor = db.practice_reading.find(query).sort("cefr_level", 1)
        docs = await cursor.to_list(length=100)

        results = []
        for d in docs:
            results.append({
                "id": d.get("id"),
                "title": d.get("title"),
                "cefr_level": d.get("cefr_level"),
                "topic": d.get("topic"),
                "difficulty": d.get("difficulty", "Easy"),
                "text_type": d.get("text_type", "passage"),
                "question_count": len(d.get("questions", [])),
                "source_material_id": d.get("source_material_id"),
                "is_seeded": bool(d.get("is_seeded", d.get("id") in {item["id"] for item in STARTING_READING_EXERCISES}))
            })
        return results

    @classmethod
    async def get_reading_exercise(cls, exercise_id: str) -> Optional[ReadingExerciseLearnerView]:
        """Fetch reading exercise for learner (hides correct answers and full translation)."""
        db = get_db()
        doc = await db.practice_reading.find_one({"id": exercise_id})
        if not doc:
            return None

        # Build learner questions
        learner_questions = []
        for q in doc.get("questions", []):
            learner_questions.append({
                "id": q.get("id"),
                "question": q.get("question"),
                "type": q.get("type", "multiple_choice"),
                "options": q.get("options", [])
            })

        return ReadingExerciseLearnerView(
            id=doc.get("id", exercise_id),
            title=doc.get("title", ""),
            cefr_level=doc.get("cefr_level", "A1"),
            topic=doc.get("topic", "General"),
            difficulty=doc.get("difficulty", "Easy"),
            text_type=doc.get("text_type", "passage"),
            is_seeded=bool(doc.get("is_seeded", doc.get("id") in {item["id"] for item in STARTING_READING_EXERCISES})),
            passage_de=doc.get("passage_de", ""),
            vocabulary_hints=doc.get("vocabulary_hints", []),
            questions=learner_questions,
            source_material_id=doc.get("source_material_id"),
            source_lesson_id=doc.get("source_lesson_id")
        )

    @classmethod
    async def evaluate_reading_submission(
        cls,
        exercise_id: str,
        user_answers: Dict[str, Any],
        time_spent_seconds: Optional[int] = None
    ) -> ReadingSubmissionResponse:
        """Evaluate submitted reading comprehension answers and persist attempt."""
        db = get_db()
        doc = await db.practice_reading.find_one({"id": exercise_id})
        if not doc:
            raise ValueError(f"Reading exercise '{exercise_id}' not found.")

        questions = doc.get("questions", [])
        if not questions:
            raise ValueError("Exercise has no questions to evaluate.")

        question_ids = {q.get("id") for q in questions}
        if set(user_answers) - question_ids:
            raise ValueError("Submission contains an unknown question ID.")

        correct_count = 0
        evaluations: List[QuestionEvaluation] = []

        for q in questions:
            qid = q.get("id")
            u_ans = user_answers.get(qid, "")
            c_ans = q.get("correct_answer")
            alternatives = q.get("acceptable_alternatives", [])
            explanation = q.get("explanation_en", "")

            u_norm = _normalize(str(u_ans))
            c_norm = _normalize(str(c_ans))

            if q.get("type") in ("multiple_choice", "true_false") and u_ans and u_ans not in q.get("options", []):
                raise ValueError(f"Invalid choice for question '{qid}'.")

            is_correct = (u_norm == c_norm)
            if not is_correct:
                for alt in alternatives:
                    if u_norm == _normalize(alt):
                        is_correct = True
                        break

            if is_correct:
                correct_count += 1

            evaluations.append(
                QuestionEvaluation(
                    question_id=qid,
                    is_correct=is_correct,
                    user_answer=u_ans,
                    correct_answer=c_ans,
                    explanation_en=explanation
                )
            )

        score = round((correct_count / len(questions)) * 100)
        is_perfect = (score == 100)
        now_iso = datetime.now(timezone.utc).isoformat()

        # Feedback text
        if is_perfect:
            feedback = "Ausgezeichnet! (Excellent!) You answered all reading comprehension questions correctly."
        elif score >= 70:
            feedback = "Gut gemacht! (Well done!) You understood most of the passage."
        else:
            feedback = "Guter Versuch! (Good try!) Review the explanations and passage translation below."

        # Persist attempt in DB
        try:
            attempt_doc = {
                "exercise_id": exercise_id,
                "user_id": "default",
                "is_seeded": False,
                "skill": "reading",
                "score": score,
                "user_answers": user_answers,
                "time_spent_seconds": time_spent_seconds,
                "timestamp": now_iso
            }
            attempt_doc["cefr_level"] = doc.get("cefr_level")
            await db.exercise_attempts.insert_one(attempt_doc)
        except Exception as e:
            logger.exception("Could not persist reading attempt")
            raise RuntimeError("Could not save the reading attempt. Please try again.") from e

        return ReadingSubmissionResponse(
            exercise_id=exercise_id,
            score=score,
            is_perfect=is_perfect,
            results=evaluations,
            translation_en=doc.get("translation_en", ""),
            feedback=feedback,
            completed_at=now_iso
        )

    # ==================== 2. Listening (Hören) ====================

    @classmethod
    async def list_listening_resources(
        cls,
        cefr_level: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        user_id: str = "default",
    ) -> List[Dict[str, Any]]:
        """List maintained external resources with real per-learner completion state."""
        resources = LISTENING_RESOURCE_CATALOG
        if cefr_level and cefr_level.upper() in {"A1", "A2", "B1"}:
            resources = [item for item in resources if item["cefr_level"] == cefr_level.upper()]
        if category and category.strip():
            wanted = category.strip().casefold()
            resources = [item for item in resources if wanted in {value.casefold() for value in item["categories"]}]
        if search and search.strip():
            term = search.strip().casefold()
            resources = [item for item in resources if term in " ".join((item["title"], item["topic"], item["description"], item["publisher"])).casefold()]

        db = get_db()
        completed_docs = await db.listening_resource_completions.find({
            "user_id": user_id,
            "resource_id": {"$in": [item["id"] for item in resources]},
        }).to_list(length=len(resources)) if resources else []
        completions = {item["resource_id"]: item.get("completed_at") for item in completed_docs}
        return [{**item, "completed_at": completions.get(item["id"])} for item in resources]

    @classmethod
    async def complete_listening_resource(cls, resource_id: str, user_id: str = "default") -> Dict[str, Any]:
        """Record the learner's explicit manual completion of an external resource."""
        resource = next((item for item in LISTENING_RESOURCE_CATALOG if item["id"] == resource_id), None)
        if not resource:
            raise ValueError(f"Listening resource '{resource_id}' not found.")
        db = get_db()
        completed_at = datetime.now(timezone.utc).isoformat()
        await db.listening_resource_completions.update_one(
            {"user_id": user_id, "resource_id": resource_id},
            {"$setOnInsert": {
                "user_id": user_id,
                "resource_id": resource_id,
                "cefr_level": resource["cefr_level"],
                "completed_at": completed_at,
            }},
            upsert=True,
        )
        saved = await db.listening_resource_completions.find_one({"user_id": user_id, "resource_id": resource_id})
        return {"resource_id": resource_id, "completed_at": saved["completed_at"]}

    @classmethod
    async def list_listening_exercises(
        cls,
        cefr_level: Optional[str] = None,
        topic: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Query listening audio passages with optional filters."""
        db = get_db()
        query: Dict[str, Any] = {}
        if cefr_level and cefr_level.strip():
            query["cefr_level"] = cefr_level.strip().upper()
        if topic and topic.strip():
            query["topic"] = {"$regex": f"^{re.escape(topic.strip())}$", "$options": "i"}

        cursor = db.practice_listening.find(query).sort("cefr_level", 1)
        docs = await cursor.to_list(length=100)

        results = []
        for d in docs:
            results.append({
                "id": d.get("id"),
                "title": d.get("title"),
                "cefr_level": d.get("cefr_level"),
                "topic": d.get("topic"),
                "difficulty": d.get("difficulty", "Easy"),
                "audio_type": d.get("audio_type", "dialogue"),
                "question_count": len(d.get("questions", [])),
                "audio_url": d.get("audio_url"),
                "source_material_id": d.get("source_material_id"),
                "is_seeded": bool(d.get("is_seeded", False))
            })
        return results

    @classmethod
    async def get_listening_exercise(cls, exercise_id: str) -> Optional[ListeningExerciseLearnerView]:
        """Fetch listening exercise (hiding audio script and translation until submission)."""
        db = get_db()
        doc = await db.practice_listening.find_one({"id": exercise_id})
        if not doc:
            return None

        learner_questions = []
        for q in doc.get("questions", []):
            learner_questions.append({
                "id": q.get("id"),
                "question": q.get("question"),
                "type": q.get("type", "multiple_choice"),
                "options": q.get("options", [])
            })

        return ListeningExerciseLearnerView(
            id=doc.get("id", exercise_id),
            title=doc.get("title", ""),
            cefr_level=doc.get("cefr_level", "A1"),
            topic=doc.get("topic", "General"),
            difficulty=doc.get("difficulty", "Easy"),
            audio_type=doc.get("audio_type", "dialogue"),
            audio_url=doc.get("audio_url"),
            audio_text=doc.get("script_de") if not doc.get("audio_url") else None,
            questions=learner_questions,
            source_material_id=doc.get("source_material_id"),
            source_lesson_id=doc.get("source_lesson_id")
        )

    @classmethod
    async def evaluate_listening_submission(
        cls,
        exercise_id: str,
        user_answers: Dict[str, Any],
        time_spent_seconds: Optional[int] = None
    ) -> ListeningSubmissionResponse:
        """Evaluate listening comprehension submission and reveal full script."""
        db = get_db()
        doc = await db.practice_listening.find_one({"id": exercise_id})
        if not doc:
            raise ValueError(f"Listening exercise '{exercise_id}' not found.")

        questions = doc.get("questions", [])
        if not questions:
            raise ValueError("Exercise has no questions to evaluate.")

        correct_count = 0
        evaluations: List[QuestionEvaluation] = []

        for q in questions:
            qid = q.get("id")
            u_ans = user_answers.get(qid, "")
            c_ans = q.get("correct_answer")
            alternatives = q.get("acceptable_alternatives", [])
            explanation = q.get("explanation_en", "")

            u_norm = _normalize(str(u_ans))
            c_norm = _normalize(str(c_ans))

            is_correct = (u_norm == c_norm)
            if not is_correct:
                for alt in alternatives:
                    if u_norm == _normalize(alt):
                        is_correct = True
                        break

            if is_correct:
                correct_count += 1

            evaluations.append(
                QuestionEvaluation(
                    question_id=qid,
                    is_correct=is_correct,
                    user_answer=u_ans,
                    correct_answer=c_ans,
                    explanation_en=explanation
                )
            )

        score = round((correct_count / len(questions)) * 100)
        is_perfect = (score == 100)
        now_iso = datetime.now(timezone.utc).isoformat()

        if is_perfect:
            feedback = "Prima! (Great!) You understood the spoken German dialogue accurately."
        elif score >= 70:
            feedback = "Gut gehört! (Well heard!) You grasped the essential details."
        else:
            feedback = "Übung macht den Meister! (Practice makes perfect!) Read along with the transcript below."

        try:
            attempt_doc = {
                "exercise_id": exercise_id,
                "user_id": "default",
                "is_seeded": False,
                "skill": "listening",
                "score": score,
                "user_answers": user_answers,
                "time_spent_seconds": time_spent_seconds,
                "cefr_level": doc.get("cefr_level"),
                "timestamp": now_iso
            }
            await db.exercise_attempts.insert_one(attempt_doc)
        except Exception as e:
            logger.exception("Could not persist listening attempt")
            raise RuntimeError("Could not save the listening attempt. Please try again.") from e

        return ListeningSubmissionResponse(
            exercise_id=exercise_id,
            score=score,
            is_perfect=is_perfect,
            results=evaluations,
            script_de=doc.get("script_de", ""),
            translation_en=doc.get("translation_en", ""),
            feedback=feedback,
            completed_at=now_iso
        )

    # ==================== 3. Writing (Schreiben) ====================

    @classmethod
    async def list_writing_prompts(
        cls,
        cefr_level: Optional[str] = None,
        topic: Optional[str] = None,
        task_type: Optional[str] = None
    ) -> List[WritingPromptBase]:
        """Query writing prompts across A1, A2, and B1."""
        db = get_db()
        query: Dict[str, Any] = {}
        if cefr_level and cefr_level.strip():
            query["cefr_level"] = cefr_level.strip().upper()
        if topic and topic.strip():
            query["topic"] = {"$regex": f"^{re.escape(topic.strip())}$", "$options": "i"}
        if task_type and task_type.strip():
            query["task_type"] = task_type.strip()

        cursor = db.practice_writing_prompts.find(query).sort("cefr_level", 1)
        docs = await cursor.to_list(length=100)

        return [WritingPromptBase(**d) for d in docs]

    @classmethod
    async def get_writing_prompt(cls, prompt_id: str) -> Optional[WritingPromptBase]:
        """Fetch single writing prompt by ID."""
        db = get_db()
        doc = await db.practice_writing_prompts.find_one({"id": prompt_id})
        return WritingPromptBase(**doc) if doc else None

    @classmethod
    async def save_writing_draft(cls, prompt_id: str, content: str, user_id: str = "default") -> WritingDraftResponse:
        """Save or update an unfinished writing draft in MongoDB."""
        db = get_db()
        now_iso = datetime.now(timezone.utc).isoformat()

        existing = await db.writing_drafts.find_one({"prompt_id": prompt_id, "user_id": user_id})
        if existing:
            await db.writing_drafts.update_one(
                {"_id": existing["_id"]},
                {"$set": {"content": content, "updated_at": now_iso}}
            )
            return WritingDraftResponse(id=str(existing["_id"]), prompt_id=prompt_id, content=content, updated_at=now_iso)
        else:
            doc = {"prompt_id": prompt_id, "user_id": user_id, "content": content, "updated_at": now_iso}
            res = await db.writing_drafts.insert_one(doc)
            return WritingDraftResponse(id=str(res.inserted_id), prompt_id=prompt_id, content=content, updated_at=now_iso)

    @classmethod
    async def get_writing_draft(cls, prompt_id: str, user_id: str = "default") -> Optional[WritingDraftResponse]:
        """Retrieve a saved writing draft for a prompt."""
        db = get_db()
        doc = await db.writing_drafts.find_one({"prompt_id": prompt_id, "user_id": user_id})
        if not doc:
            return None
        return WritingDraftResponse(id=str(doc["_id"]), prompt_id=prompt_id, content=doc.get("content", ""), updated_at=doc.get("updated_at", ""))

    @classmethod
    async def delete_writing_draft(cls, draft_id: str) -> bool:
        """Remove a writing draft."""
        db = get_db()
        try:
            oid = ObjectId(draft_id) if ObjectId.is_valid(draft_id) else draft_id
            res = await db.writing_drafts.delete_one({"_id": oid} if isinstance(oid, ObjectId) else {"id": str(oid)})
            return res.deleted_count > 0
        except Exception:
            return False

    @classmethod
    def _deterministic_writing_check(cls, text: str, prompt: Optional[WritingPromptBase], level: str) -> Dict[str, Any]:
        """
        Rule-based German grammar, capitalization, and sentence structure evaluation.
        Used as a reliable local fallback when Ollama is unavailable.
        """
        grammar_mistakes = []
        word_order_mistakes = []
        article_mistakes = []
        spelling_mistakes = []
        suggestions = []

        words = re.findall(r'\b\w+\b', text)
        word_count = len(words)

        # 1. Capitalization check (German nouns must be capitalized)
        common_lower_nouns = {
            "apfel": "Apfel", "buch": "Buch", "auto": "Auto", "kaffee": "Kaffee",
            "tag": "Tag", "morgen": "Morgen", "abend": "Abend", "woche": "Woche",
            "freund": "Freund", "freundin": "Freundin", "deutsch": "Deutsch",
            "zeit": "Zeit", "haus": "Haus", "stadt": "Stadt", "schule": "Schule",
            "arbeit": "Arbeit", "beruf": "Beruf", "essen": "Essen", "zimmer": "Zimmer"
        }
        for w in words:
            if w.lower() in common_lower_nouns and w[0].islower():
                spelling_mistakes.append(f"'{w}' should be capitalized as '{common_lower_nouns[w.lower()]}' because all German nouns are capitalized.")

        # 2. Check subject pronoun 'ich'
        if not re.search(r'\b(ich|wir|du|er|sie|es)\b', text, re.IGNORECASE):
            grammar_mistakes.append("Remember to include subject pronouns (ich, wir, du...) with your conjugated verbs.")

        # 3. Subordinate clause check for B1 / A2
        if re.search(r'\b(weil|dass|obwohl|wenn)\b', text, re.IGNORECASE):
            suggestions.append("Check that in your subordinate clause (with weil/dass/obwohl/wenn), the conjugated verb is placed at the very end.")

        # 4. Corrected text construction
        corrected = text
        for lower_w, cap_w in common_lower_nouns.items():
            corrected = re.sub(r'\b' + lower_w + r'\b', cap_w, corrected)

        # Calculate score based on errors detected and length
        error_count = len(grammar_mistakes) + len(word_order_mistakes) + len(spelling_mistakes)
        base_score = 95 - (error_count * 10)
        if word_count < 10:
            base_score = max(50, base_score - 15)
        score = max(50, min(100, base_score))

        explanation = (
            f"Evaluated against standard CEFR {level} grammar rules. "
            "Verified German capitalization rules, subject-verb presence, and basic sentence structure."
        )

        return {
            "corrected_text": corrected,
            "grammar_mistakes": grammar_mistakes,
            "word_order_mistakes": word_order_mistakes,
            "article_mistakes": article_mistakes,
            "spelling_mistakes": spelling_mistakes,
            "explanation_en": explanation,
            "natural_alternative_de": prompt.sample_solution_de if prompt else None,
            "suggestions": suggestions or ["Keep practicing! For more detailed conversational analysis, start Ollama locally."],
            "score": score,
            "is_ai_evaluated": False,
            "evaluation_source": "deterministic_rules"
        }

    @classmethod
    async def evaluate_writing_submission(
        cls,
        prompt_id: str,
        content: str,
        cefr_level: str = "A1",
        time_spent_seconds: Optional[int] = None,
        user_id: str = "default"
    ) -> WritingEvaluationResponse:
        """
        Evaluate writing response using Ollama local AI when available,
        falling back to deterministic checks if Ollama is offline.
        """
        clean_text = content.strip()
        if not clean_text:
            raise ValueError("Writing submission cannot be empty.")

        prompt = await cls.get_writing_prompt(prompt_id)
        level = (cefr_level or (prompt.cefr_level if prompt else "A1")).upper()
        now_iso = datetime.now(timezone.utc).isoformat()

        eval_result = None

        # Try local Ollama evaluation
        try:
            status = await OllamaService.check_status()
            if status.get("is_ready"):
                system_prompt = (
                    "You are Klara, an expert German language teacher. Evaluate the learner's German writing submission.\n"
                    f"The learner's target CEFR level is {level}.\n"
                    "Output ONLY a valid JSON object matching this schema without any markdown commentary outside the JSON:\n"
                    "{\n"
                    '  "corrected_text": "Corrected German text preserving learner\'s meaning",\n'
                    '  "grammar_mistakes": ["Specific grammar errors with brief reasons"],\n'
                    '  "word_order_mistakes": ["Word order issues (e.g. verb position)"],\n'
                    '  "article_mistakes": ["Gender or case errors"],\n'
                    '  "spelling_mistakes": ["Spelling and capitalization errors (German nouns)"],\n'
                    '  "explanation_en": "Clear, encouraging explanation in simple English",\n'
                    '  "natural_alternative_de": "A more natural, idiomatic phrasing in German",\n'
                    '  "suggestions": ["1-2 actionable tips for improvement"],\n'
                    '  "score": 85 // integer 0 to 100 based on level-appropriate accuracy\n'
                    "}"
                )

                user_prompt = (
                    f"Writing Prompt: {prompt.title if prompt else 'German Practice'}\n"
                    f"Instruction: {prompt.instruction_en if prompt else 'Write in German'}\n"
                    f"Reference Solution: {prompt.sample_solution_de if prompt else 'N/A'}\n\n"
                    f"Learner's German Submission:\n{clean_text}\n"
                )

                ai_response = await OllamaService.generate_chat(
                    messages=[{"role": "user", "content": user_prompt}],
                    system_prompt=system_prompt,
                    temperature=0.2,
                    timeout=20.0
                )

                # Parse JSON
                fence_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', ai_response)
                json_str = fence_match.group(1).strip() if fence_match else ai_response.strip()
                s_idx = json_str.find('{')
                e_idx = json_str.rfind('}')
                if s_idx != -1 and e_idx != -1:
                    parsed = json.loads(json_str[s_idx:e_idx+1])
                    eval_result = {
                        "corrected_text": parsed.get("corrected_text") or clean_text,
                        "grammar_mistakes": parsed.get("grammar_mistakes") or [],
                        "word_order_mistakes": parsed.get("word_order_mistakes") or [],
                        "article_mistakes": parsed.get("article_mistakes") or [],
                        "spelling_mistakes": parsed.get("spelling_mistakes") or [],
                        "explanation_en": parsed.get("explanation_en") or "Good effort! Reviewed your grammar and sentence structure.",
                        "natural_alternative_de": parsed.get("natural_alternative_de") or (prompt.sample_solution_de if prompt else None),
                        "suggestions": parsed.get("suggestions") or [],
                        "score": max(0, min(100, int(parsed.get("score", 80)))),
                        "is_ai_evaluated": True,
                        "evaluation_source": "ollama"
                    }
        except Exception as e:
            logger.info(f"Ollama writing evaluation unavailable or failed ({e}); falling back to deterministic check.")

        # Fallback to rule-based evaluation
        if not eval_result:
            eval_result = cls._deterministic_writing_check(clean_text, prompt, level)

        submission_id = f"sub_{uuid.uuid4().hex[:12]}"
        response_model = WritingEvaluationResponse(
            id=submission_id,
            prompt_id=prompt_id,
            original_text=clean_text,
            corrected_text=eval_result["corrected_text"],
            grammar_mistakes=eval_result["grammar_mistakes"],
            word_order_mistakes=eval_result["word_order_mistakes"],
            article_mistakes=eval_result["article_mistakes"],
            spelling_mistakes=eval_result["spelling_mistakes"],
            explanation_en=eval_result["explanation_en"],
            natural_alternative_de=eval_result.get("natural_alternative_de"),
            suggestions=eval_result["suggestions"],
            score=eval_result["score"],
            is_ai_evaluated=eval_result["is_ai_evaluated"],
            evaluation_source=eval_result["evaluation_source"],
            timestamp=now_iso
        )

        # Persist submission and attempt in DB
        db = get_db()
        try:
            sub_doc = response_model.model_dump()
            sub_doc["user_id"] = user_id
            sub_doc["cefr_level"] = level
            await db.writing_submissions.insert_one(sub_doc)

            # Record in exercise_attempts for unified stats
            await db.exercise_attempts.insert_one({
                "exercise_id": prompt_id,
                "user_id": user_id,
                "is_seeded": False,
                "skill": "writing",
                "score": eval_result["score"],
                "user_response": clean_text,
                "time_spent_seconds": time_spent_seconds,
                "cefr_level": level,
                "timestamp": now_iso
            })
        except Exception as db_err:
            logger.exception("Failed to record writing submission")
            raise RuntimeError("Could not save the writing submission. Please try again.") from db_err

        return response_model

    @classmethod
    async def list_writing_submissions(cls, prompt_id: Optional[str] = None, user_id: str = "default", limit: int = 20) -> List[WritingEvaluationResponse]:
        """Fetch historical writing submissions."""
        db = get_db()
        query: Dict[str, Any] = {"user_id": user_id}
        if prompt_id:
            query["prompt_id"] = prompt_id

        cursor = db.writing_submissions.find(query).sort("timestamp", -1).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [WritingEvaluationResponse(**d) for d in docs]

    # ==================== 4. Speaking (Sprechen) ====================

    @classmethod
    async def list_speaking_scenarios(
        cls,
        cefr_level: Optional[str] = None,
        topic: Optional[str] = None
    ) -> List[SpeakingScenario]:
        """List speaking scenarios and guided role-plays."""
        db = get_db()
        query: Dict[str, Any] = {}
        if cefr_level and cefr_level.strip():
            query["cefr_level"] = cefr_level.strip().upper()
        if topic and topic.strip():
            query["topic"] = {"$regex": f"^{re.escape(topic.strip())}$", "$options": "i"}

        cursor = db.practice_speaking_scenarios.find(query).sort("cefr_level", 1)
        docs = await cursor.to_list(length=100)

        return [SpeakingScenario(**d) for d in docs]

    @classmethod
    async def start_speaking_session(
        cls,
        scenario_id: Optional[str] = None,
        cefr_level: str = "A1",
        topic: Optional[str] = None,
        user_id: str = "default"
    ) -> SpeakingMessageResponse:
        """Start a new speaking practice conversation session."""
        db = get_db()
        scenario = None
        if scenario_id:
            scenario_doc = await db.practice_speaking_scenarios.find_one({"id": scenario_id})
            if scenario_doc:
                scenario = SpeakingScenario(**scenario_doc)
        if not scenario:
            raise ValueError(f"Speaking scenario '{scenario_id or ''}' not found.")

        level = scenario.cefr_level.upper()
        initial_text = scenario.initial_prompt_de
        initial_trans = scenario.initial_translation_en

        session_id = f"spk_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()

        session_doc = {
            "session_id": session_id,
            "scenario_id": scenario_id,
            "user_id": user_id,
            "is_seeded": False,
            "cefr_level": level,
            "topic": scenario.topic,
            "scenario_guide": scenario.scenario_guide,
            "messages": [
                {
                    "role": "assistant",
                    "text_de": initial_text,
                    "translation_en": initial_trans,
                    "timestamp": now_iso
                }
            ],
            "turn_count": 1,
            "created_at": now_iso,
            "updated_at": now_iso
        }

        await db.speaking_sessions.insert_one(session_doc)

        return SpeakingMessageResponse(
            session_id=session_id,
            role="assistant",
            text_de=initial_text,
            translation_en=initial_trans,
            corrections=None,
            turn_count=1,
            timestamp=now_iso
        )

    @classmethod
    async def send_speaking_message(
        cls,
        session_id: str,
        message: str,
        audio_url: Optional[str] = None,
        user_id: str = "default"
    ) -> SpeakingMessageResponse:
        """Send a learner spoken message and receive next tutor turn with feedback."""
        clean_msg = message.strip()
        if not clean_msg:
            raise ValueError("Message cannot be empty.")

        db = get_db()
        session = await db.speaking_sessions.find_one({"session_id": session_id})
        if not session:
            raise ValueError(f"Speaking session '{session_id}' not found.")

        level = session.get("cefr_level", "A1")
        now_iso = datetime.now(timezone.utc).isoformat()

        # Build prompt for conversational speaking partner
        tutor_reply_de = ""
        tutor_trans_en = ""
        corrections = None

        try:
            status = await OllamaService.check_status()
            if status.get("is_ready"):
                history = session.get("messages", [])[-6:]
                conv_history_lines = []
                for m in history:
                    r = "Learner" if m.get("role") == "user" else "Tutor"
                    conv_history_lines.append(f"{r}: {m.get('text_de', '')}")

                sys_prompt = (
                    f"You are Klara, an encouraging German speaking partner for a CEFR {level} learner.\n"
                    f"Scenario: {session.get('topic')} ({session.get('scenario_guide')})\n"
                    "Instructions:\n"
                    f"1. Respond in natural, level-appropriate CEFR {level} German.\n"
                    "2. Ask exactly ONE clear follow-up question to keep the conversation going.\n"
                    "3. If the learner made a notable grammar mistake, provide a gentle 1-sentence correction in English.\n"
                    "Output ONLY a valid JSON object in this format:\n"
                    "{\n"
                    '  "reply_de": "Your German response + ONE follow-up question",\n'
                    '  "translation_en": "English translation of your reply",\n'
                    '  "correction_en": "Optional gentle correction note, or null if fine"\n'
                    "}"
                )

                user_prompt = (
                    f"Conversation so far:\n" + "\n".join(conv_history_lines) + "\n\n"
                    f"Learner just said: \"{clean_msg}\"\n"
                )

                ai_resp = await OllamaService.generate_chat(
                    messages=[{"role": "user", "content": user_prompt}],
                    system_prompt=sys_prompt,
                    temperature=0.3,
                    timeout=20.0
                )

                s_idx = ai_resp.find('{')
                e_idx = ai_resp.rfind('}')
                if s_idx != -1 and e_idx != -1:
                    parsed = json.loads(ai_resp[s_idx:e_idx+1])
                    tutor_reply_de = parsed.get("reply_de", "")
                    tutor_trans_en = parsed.get("translation_en", "")
                    corr_note = parsed.get("correction_en")
                    if corr_note:
                        corrections = {"note": corr_note}
        except Exception as e:
            logger.info(f"Ollama speaking partner unavailable ({e}).")
            raise RuntimeError("The local AI speaking partner is unavailable. Your message was not saved; please try again later.") from e

        if not tutor_reply_de:
            raise RuntimeError("The local AI did not return a speaking response. Your message was not saved; please try again.")

        # Append messages to session
        user_turn = {
            "role": "user",
            "text_de": clean_msg,
            "audio_url": audio_url,
            "timestamp": now_iso
        }
        assistant_turn = {
            "role": "assistant",
            "text_de": tutor_reply_de,
            "translation_en": tutor_trans_en,
            "corrections": corrections,
            "timestamp": now_iso
        }

        turn_count = session.get("turn_count", 1) + 1
        await db.speaking_sessions.update_one(
            {"_id": session["_id"]},
            {
                "$push": {"messages": {"$each": [user_turn, assistant_turn]}},
                "$set": {"updated_at": now_iso, "turn_count": turn_count}
            }
        )

        return SpeakingMessageResponse(
            session_id=session_id,
            role="assistant",
            text_de=tutor_reply_de,
            translation_en=tutor_trans_en,
            corrections=corrections,
            turn_count=turn_count,
            timestamp=now_iso
        )

    @classmethod
    async def get_speaking_session(cls, session_id: str) -> Optional[Dict[str, Any]]:
        """Get full conversation history of a speaking session."""
        db = get_db()
        doc = await db.speaking_sessions.find_one({"session_id": session_id})
        if not doc:
            return None
        doc["_id"] = str(doc["_id"])
        return doc

    # ==================== 5. Progress & Analytics ====================

    @classmethod
    async def get_practice_progress(cls, user_id: str = "default") -> PracticeProgressResponse:
        """Calculate real aggregated practice progress across all 4 language skills."""
        db = get_db()

        # Query all attempts
        attempts = await db.exercise_attempts.find({"user_id": user_id, "is_seeded": False}).sort("timestamp", -1).to_list(length=5000)
        resource_completions = await db.listening_resource_completions.find({"user_id": user_id}).to_list(length=5000)

        skill_buckets: Dict[str, List[int]] = {
            "reading": [],
            "listening": [],
            "writing": [],
            "speaking": []
        }
        time_buckets: Dict[str, int] = {
            "reading": 0,
            "listening": 0,
            "writing": 0,
            "speaking": 0
        }
        recent_activity: List[Dict[str, Any]] = []

        for att in attempts:
            skill = str(att.get("skill", "")).lower()
            if skill in skill_buckets:
                score = att.get("score")
                seconds = att.get("time_spent_seconds") or 0
                time_buckets[skill] += seconds

                if isinstance(score, (int, float)):
                    skill_buckets[skill].append(int(score))
                if isinstance(score, (int, float)) and len(recent_activity) < 10:
                    recent_activity.append({
                        "exercise_id": att.get("exercise_id"),
                        "skill": skill,
                        "score": score,
                        "timestamp": att.get("timestamp")
                    })

        recent_activity.extend({
            "resource_id": item.get("resource_id"),
            "skill": "listening",
            "completed": True,
            "cefr_level": item.get("cefr_level"),
            "timestamp": item.get("completed_at"),
        } for item in resource_completions)
        recent_activity.sort(key=lambda item: str(item.get("timestamp") or ""), reverse=True)
        recent_activity = recent_activity[:10]

        def make_metric(skill_key: str) -> SkillMetric:
            scores = skill_buckets.get(skill_key, [])
            count = len(scores)
            avg = round(sum(scores) / count) if count > 0 else None
            mins = round(time_buckets.get(skill_key, 0) / 60)
            return SkillMetric(completed_count=count, average_score=avg, total_time_minutes=mins)

        reading_m = make_metric("reading")
        listening_m = make_metric("listening")
        # External completions count as listening activities, but never contribute
        # a fabricated score or duration.
        listening_m.completed_count += len(resource_completions)
        writing_m = make_metric("writing")
        speaking_m = make_metric("speaking")

        # Derive streak only from persisted activity dates.
        streak = 0
        activity_dates = set()
        for att in attempts:
            stamp = att.get("timestamp")
            try:
                parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00")) if isinstance(stamp, str) else stamp
                if parsed:
                    activity_dates.add(parsed.astimezone(timezone.utc).date())
            except (ValueError, TypeError, AttributeError):
                continue
        for item in resource_completions:
            stamp = item.get("completed_at")
            try:
                parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00")) if isinstance(stamp, str) else stamp
                if parsed:
                    activity_dates.add(parsed.astimezone(timezone.utc).date())
            except (ValueError, TypeError, AttributeError):
                continue
        today = datetime.now(timezone.utc).date()
        cursor = today if today in activity_dates else today - timedelta(days=1)
        while cursor in activity_dates:
            streak += 1
            cursor -= timedelta(days=1)

        # Overall skill scores mapping
        overall = {
            "reading": reading_m.average_score if reading_m.completed_count > 0 else None,
            "listening": listening_m.average_score if listening_m.completed_count > 0 else None,
            "writing": writing_m.average_score if writing_m.completed_count > 0 else None,
            "speaking": speaking_m.average_score if speaking_m.completed_count > 0 else None
        }

        # CEFR breakdown
        cefr_breakdown = {
            level: len([a for a in attempts if a.get("cefr_level") == level])
            + len([item for item in resource_completions if item.get("cefr_level") == level])
            for level in ("A1", "A2", "B1")
        }

        total_time = sum(time_buckets.values()) // 60

        return PracticeProgressResponse(
            overall_skill_scores=overall,
            reading=reading_m,
            listening=listening_m,
            writing=writing_m,
            speaking=speaking_m,
            total_completed=len(attempts) + len(resource_completions),
            total_study_minutes=total_time,
            streak_days=streak,
            recent_activity=recent_activity,
            cefr_breakdown=cefr_breakdown
        )
