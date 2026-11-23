import re
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from bson import ObjectId

from app.database import get_db
from app.security import current_user_id
from app.models.exercise import ExerciseLearnerView
from app.services.material_intelligence_service import MaterialIntelligenceService


def _id_query(value: str) -> Dict[str, Any]:
    return {"_id": ObjectId(value)} if ObjectId.is_valid(value) else {"id": value}


def _render_notes(content: Dict[str, Any]) -> str:
    lines = []
    if content.get("introduction"):
        lines.extend(["## Overview", "", f"- {str(content['introduction']).strip()}", ""])
    for key, title in (
        ("concepts", "Key concepts"),
        ("grammar", "Grammar"),
        ("vocabulary", "Vocabulary"),
        ("examples", "Examples"),
        ("rules", "Important rules"),
        ("common_mistakes", "Common mistakes"),
    ):
        entries = content.get(key) or []
        if not entries:
            continue
        lines.extend([f"## {title}", ""])
        for entry in entries:
            if key == "concepts":
                label = entry.get("title")
                detail = entry.get("explanation")
                bullet = f"**{str(label).strip()}:** {str(detail).strip()}" if label and detail else str(label or detail or "").strip()
            elif key == "grammar":
                label = entry.get("concept")
                detail = entry.get("explanation") or entry.get("rule")
                rule = entry.get("rule") if entry.get("explanation") else None
                bullet = f"**{str(label).strip()}:** {str(detail).strip()}" if label and detail else str(label or detail or "").strip()
                if rule:
                    bullet += f" Rule: {str(rule).strip()}"
            elif key == "vocabulary":
                word = str(entry.get("word") or "").strip()
                article = str(entry.get("article") or "").strip()
                label = f"{article} {word}".strip()
                details = [str(entry[field]).strip() for field in ("meaning_en", "plural", "example_de", "example_en") if entry.get(field)]
                bullet = f"**{label}:** " + "; ".join(details) if label else "; ".join(details)
            elif key == "examples":
                german, english = entry.get("german"), entry.get("english")
                bullet = f"**{str(german).strip()}** — {str(english).strip()}" if german and english else str(german or english or "").strip()
            elif key == "common_mistakes":
                mistake, correction, explanation = entry.get("mistake"), entry.get("correction"), entry.get("explanation")
                bullet = f"**{str(mistake).strip()}** → **{str(correction).strip()}**" if mistake and correction else str(mistake or correction or "").strip()
                if explanation:
                    bullet += f" — {str(explanation).strip()}"
            else:
                bullet = str(entry.get("text") or "").strip()
            values = [bullet] if bullet else []
            if entry.get("generated") is True:
                values.append("*Generated practice example*")
            source_ref = (content.get("source_references") or {}).get(entry.get("source_id"))
            if source_ref:
                values.append(f"*Source: {source_ref}*")
            if values:
                lines.append("- " + "  ".join(values))
        lines.append("")
    if content.get("summary"):
        lines.extend(["## Quick revision", ""])
        summary_points = [part.strip(" \t-•") for part in re.split(r"\n+|(?<=[.!?])\s+", str(content["summary"])) if part.strip(" \t-•")]
        lines.extend(f"- {point}" for point in summary_points)
        lines.append("")
    return "\n".join(lines).strip()


class StudyService:
    @classmethod
    async def list_notes(cls, material_id: Optional[str] = None) -> List[Dict[str, Any]]:
        db = get_db()
        query: Dict[str, Any] = {"user_id": current_user_id(), "is_current": True}
        if material_id:
            query["material_id"] = material_id
        notes = await db.study_notes.find(query).sort("updated_at", -1).to_list(length=500)
        result = []
        for note in notes:
            material = await db.materials.find_one({"_id": ObjectId(note["material_id"]), "user_id": current_user_id(), "is_seeded": {"$ne": True}}) if ObjectId.is_valid(note["material_id"]) else None
            if not material:
                continue
            result.append(cls._note_view(note, material))
        return result

    @staticmethod
    def _note_view(note: Dict[str, Any], material: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": str(note.get("_id", note.get("id", ""))),
            "material_id": note["material_id"],
            "material_title": material.get("title"),
            "title": note.get("title", "Study Notes"),
            "cefr_level": note.get("cefr_level", "Unknown"),
            "topic": note.get("topic", "General"),
            "content": note.get("content", {}),
            "markdown": note.get("manual_markdown") or _render_notes(note.get("content", {})),
            "version": note.get("version", 1),
            "is_manually_edited": note.get("is_manually_edited", False),
            "updated_at": note.get("updated_at"),
        }

    @classmethod
    async def get_note(cls, note_id: str) -> Dict[str, Any]:
        note = await get_db().study_notes.find_one({**_id_query(note_id), "user_id": current_user_id()})
        if not note:
            raise ValueError("Study notes not found.")
        material = await get_db().materials.find_one({"_id": ObjectId(note["material_id"]), "user_id": current_user_id(), "is_seeded": {"$ne": True}})
        if not material:
            raise ValueError("The source material is no longer available.")
        return cls._note_view(note, material)

    @classmethod
    async def save_notes(cls, note_id: str, markdown: str) -> Dict[str, Any]:
        text = markdown.strip()
        if not text:
            raise ValueError("Notes cannot be empty.")
        result = await get_db().study_notes.update_one(
            {**_id_query(note_id), "user_id": current_user_id()},
            {"$set": {"manual_markdown": text, "is_manually_edited": True, "updated_at": datetime.now(timezone.utc).isoformat()}},
        )
        if not result.matched_count:
            raise ValueError("Study notes not found.")
        return await cls.get_note(note_id)

    @classmethod
    async def regenerate_notes(cls, note_id: str) -> Dict[str, Any]:
        previous = await get_db().study_notes.find_one({**_id_query(note_id), "user_id": current_user_id()})
        if not previous:
            raise ValueError("Study notes not found.")
        new_note = await MaterialIntelligenceService.regenerate_notes(previous["material_id"], previous)
        return await cls.get_note(str(new_note["_id"]))

    @classmethod
    async def delete_note(cls, note_id: str) -> None:
        db = get_db()
        note = await db.study_notes.find_one({**_id_query(note_id), "user_id": current_user_id()})
        if not note:
            raise ValueError("Study notes not found.")
        result = await db.study_notes.delete_one({"_id": note["_id"], "user_id": current_user_id()})
        if not result.deleted_count:
            raise ValueError("Study notes not found.")
        count = await db.study_notes.count_documents({"material_id": note["material_id"], "user_id": current_user_id(), "is_current": True})
        if ObjectId.is_valid(note["material_id"]):
            await db.materials.update_one({"_id": ObjectId(note["material_id"]), "user_id": current_user_id()}, {"$set": {"notes_count": count}})

    @classmethod
    async def list_questions(
        cls,
        material_id: Optional[str] = None,
        cefr_level: Optional[str] = None,
        topic: Optional[str] = None,
        difficulty: Optional[str] = None,
        question_type: Optional[str] = None,
        skill: Optional[str] = None,
        incorrect_only: bool = False,
    ) -> List[Dict[str, Any]]:
        db = get_db()
        query: Dict[str, Any] = {
            "user_id": current_user_id(), "is_seeded": {"$ne": True},
            "origin": {"$in": ["ai_generated", "source_generated"]},
        }
        if material_id:
            query["material_id"] = material_id
        if cefr_level:
            query["cefr_level"] = cefr_level
        if topic:
            query["topic"] = topic
        if difficulty:
            query["difficulty"] = difficulty.title()
        if question_type:
            query["type"] = question_type
        if skill:
            query["skill"] = skill
        if incorrect_only:
            attempts = await db.exercise_attempts.find({"user_id": current_user_id(), "is_seeded": False}).sort("timestamp", -1).to_list(length=10000)
            latest = {}
            for attempt in attempts:
                latest.setdefault(attempt.get("exercise_id"), attempt.get("is_correct"))
            wrong_ids = [exercise_id for exercise_id, correct in latest.items() if correct is False]
            query["id"] = {"$in": wrong_ids}
        docs = await db.exercises.find(query).sort("created_at", -1).to_list(length=1000)
        result = []
        for doc in docs:
            material = await db.materials.find_one({"_id": ObjectId(doc["material_id"]), "user_id": current_user_id(), "is_seeded": {"$ne": True}}) if ObjectId.is_valid(str(doc.get("material_id", ""))) else None
            if not material:
                continue
            item = ExerciseLearnerView(**doc).model_dump()
            item.update({"material_id": doc["material_id"], "material_title": material.get("title"), "source_ref": doc.get("source_ref"), "origin": doc.get("origin"), "source_type": doc.get("source_type")})
            result.append(item)
        return result
