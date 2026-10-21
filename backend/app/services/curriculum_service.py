import logging
from typing import Optional, List, Dict, Any
from bson import ObjectId
from app.data.curriculum_a1 import A1_LESSONS
from app.data.curriculum_a2 import A2_LESSONS
from app.data.curriculum_b1 import B1_LESSONS
from app.database import get_db

logger = logging.getLogger("german_app.curriculum")

# Static catalogue lookup
ALL_STATIC_LESSONS: List[Dict[str, Any]] = [*A1_LESSONS, *A2_LESSONS, *B1_LESSONS]
STATIC_LESSONS_BY_ID = {l["id"]: l for l in ALL_STATIC_LESSONS}

class CurriculumService:
    @staticmethod
    async def get_user_completed_lesson_ids(user_id: Optional[str] = None) -> set:
        """Returns set of completed lesson IDs for learner."""
        db = get_db()
        progress = await db.progress.find_one({"user_id": "default", "is_seeded": False})
        return set(progress.get("completed_lessons", [])) if progress else set()

    @staticmethod
    async def list_lessons(
        level: Optional[str] = None,
        topic: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Lists all lessons (static curriculum + custom study lessons generated from uploaded materials)."""
        completed_ids = await CurriculumService.get_user_completed_lesson_ids()
        lessons_list = []

        # 1. Built-in curriculum
        for l in ALL_STATIC_LESSONS:
            if level and l["cefr_level"].upper() != level.upper():
                continue
            if topic and topic.lower() not in l["topic"].lower():
                continue

            summary = {
                "id": l["id"],
                "title": l["title"],
                "cefr_level": l["cefr_level"],
                "module_title": l["module_title"],
                "topic": l["topic"],
                "order": l["order"],
                "estimated_minutes": l.get("estimated_minutes", 15),
                "objectives": l.get("objectives", []),
                "is_completed": l["id"] in completed_ids,
                "exercises_count": len(l.get("exercises", [])),
                "source_material_id": l.get("source_material_id")
            }
            lessons_list.append(summary)

        # 2. Dynamic lessons created from user materials in MongoDB
        db = get_db()
        query = {}
        if level:
            query["cefr_level"] = level.upper()
        if topic:
            query["topic"] = {"$regex": topic, "$options": "i"}

        cursor = db.lessons.find(query).sort("order", 1)
        async for doc in cursor:
            doc_id = str(doc.get("_id"))
            summary = {
                "id": doc_id,
                "title": doc.get("title", "Custom Study Lesson"),
                "cefr_level": doc.get("cefr_level", "A1"),
                "module_title": doc.get("module_title", "Uploaded Study Materials"),
                "topic": doc.get("topic", "Material Practice"),
                "order": doc.get("order", 99),
                "estimated_minutes": doc.get("estimated_minutes", 15),
                "objectives": doc.get("objectives", []),
                "is_completed": doc_id in completed_ids,
                "exercises_count": len(doc.get("exercises", [])),
                "source_material_id": doc.get("source_material_id")
            }
            lessons_list.append(summary)

        return lessons_list

    @staticmethod
    async def get_lesson(lesson_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves full lesson content by ID."""
        completed_ids = await CurriculumService.get_user_completed_lesson_ids()

        # Check static catalog first
        if lesson_id in STATIC_LESSONS_BY_ID:
            lesson = dict(STATIC_LESSONS_BY_ID[lesson_id])
            lesson["is_completed"] = lesson_id in completed_ids
            raw_ex = lesson.get("exercises", [])
            lesson["exercises_count"] = len(raw_ex)
            # Create learner-safe views for attached exercises
            learner_ex = []
            for e in raw_ex:
                copy_e = dict(e)
                copy_e.pop("correct_answer", None)
                copy_e.pop("acceptable_alternatives", None)
                copy_e.pop("explanation_en", None)
                learner_ex.append(copy_e)
            lesson["exercises"] = learner_ex
            return lesson

        # Otherwise check MongoDB
        db = get_db()
        query = {"_id": ObjectId(lesson_id)} if ObjectId.is_valid(lesson_id) else {"id": lesson_id}
        doc = await db.lessons.find_one(query)
        if doc:
            doc_id = str(doc.get("_id"))
            doc["id"] = doc_id
            doc["is_completed"] = doc_id in completed_ids
            raw_ex = doc.get("exercises", [])
            doc["exercises_count"] = len(raw_ex)
            learner_ex = []
            for e in raw_ex:
                copy_e = dict(e)
                copy_e.pop("correct_answer", None)
                copy_e.pop("acceptable_alternatives", None)
                copy_e.pop("explanation_en", None)
                learner_ex.append(copy_e)
            doc["exercises"] = learner_ex
            return doc

        return None

    @staticmethod
    async def mark_lesson_completed(lesson_id: str) -> bool:
        """Marks a lesson as completed in learner progress."""
        db = get_db()
        if lesson_id not in STATIC_LESSONS_BY_ID and not await db.lessons.find_one({"_id": ObjectId(lesson_id)} if ObjectId.is_valid(lesson_id) else {"id": lesson_id}):
            return False
        await db.progress.update_one(
            {"user_id": "default", "is_seeded": False},
            {
                "$addToSet": {"completed_lessons": lesson_id},
                "$set": {"is_seeded": False},
            },
            upsert=True
        )
        return True

    @staticmethod
    async def create_lesson_from_material(
        material_id: str,
        title: Optional[str] = None,
        cefr_level: Optional[str] = None,
        topic: Optional[str] = None,
        module_title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Creates a structured study lesson derived from an uploaded Study Library material."""
        db = get_db()
        mat_query = {"_id": ObjectId(material_id)} if ObjectId.is_valid(material_id) else {"id": material_id}
        material = await db.materials.find_one(mat_query)
        if not material:
            raise ValueError(f"Material with ID {material_id} not found")

        extracted_text = material.get("extracted_text") or ""
        if not extracted_text.strip():
            raise ValueError("This material has no extracted text to create a study session from.")
        mat_title = material.get("title") or "Study Material"
        resolved_level = cefr_level or material.get("cefr_level") or "A1"
        resolved_topic = topic or material.get("topic") or "General"
        resolved_title = title or f"Study Session: {mat_title}"

        new_lesson = {
            "title": resolved_title,
            "cefr_level": resolved_level,
            "module_title": module_title or "Uploaded Study Materials",
            "topic": resolved_topic,
            "order": 100,
            "estimated_minutes": 15,
            "objectives": ["Review the extracted source text.", "Note unfamiliar German words for vocabulary review."],
            "explanation_en": f"This study page links to text extracted from your saved material, '{mat_title}'. It does not contain generated grammar explanations or practice questions.",
            "grammar_rules": [],
            "examples": [],
            "vocabulary": [],
            "common_mistakes": [],
            "summary_en": f"Review the extracted text from your saved material, '{mat_title}'.",
            "source_material_id": str(material.get("_id") or material_id),
            "source_material_title": mat_title,
            "source_text": extracted_text,
            "exercises": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        res = await db.lessons.insert_one(new_lesson)
        new_lesson["id"] = str(res.inserted_id)
        new_lesson["_id"] = str(res.inserted_id)
        return new_lesson
