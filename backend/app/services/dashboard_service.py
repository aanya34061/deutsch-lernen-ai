from datetime import datetime, timezone, timedelta
from typing import Dict, List

from app.database import get_db
from app.models.progress import DashboardSummaryResponse, DailyStats, SkillScores
from app.models.material import MaterialResponse
from app.models.vocabulary import VocabularyResponse
from app.data.curriculum_a1 import A1_LESSONS
from app.data.curriculum_a2 import A2_LESSONS
from app.data.curriculum_b1 import B1_LESSONS


class DashboardService:
    @staticmethod
    async def get_dashboard_summary() -> DashboardSummaryResponse:
        db = get_db()
        # The app currently has one learner identity. Scope every progress source
        # to that identity instead of selecting the first unseeded database record.
        user = await db.users.find_one({"username": "learner", "is_seeded": False})

        attempts = await db.exercise_attempts.find({"user_id": "default", "is_seeded": False}).sort("timestamp", -1).to_list(length=5000)
        speaking_sessions = await db.speaking_sessions.find({"user_id": "default", "is_seeded": False}).to_list(length=5000)
        listening_completions = await db.listening_resource_completions.find({"user_id": "default"}).to_list(length=5000)
        now = datetime.now(timezone.utc)
        today = now.astimezone().date()
        today_attempts = []
        active_dates = set()
        score_buckets: Dict[str, List[int]] = {"reading": [], "listening": [], "writing": [], "speaking": []}
        today_seconds = 0
        for attempt in attempts:
            stamp = attempt.get("timestamp")
            try:
                parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00")) if isinstance(stamp, str) else stamp
                if parsed and parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                if parsed:
                    active_date = parsed.astimezone().date()
                    active_dates.add(active_date)
                    if active_date == today:
                        today_attempts.append(attempt)
                        today_seconds += max(0, int(attempt.get("time_spent_seconds") or 0))
            except (ValueError, TypeError, AttributeError):
                continue
            skill = str(attempt.get("skill", "")).lower()
            score = attempt.get("score")
            if skill in score_buckets and isinstance(score, (int, float)):
                score_buckets[skill].append(int(score))

        completed_speaking_sessions = 0
        for session in speaking_sessions:
            if any(message.get("role") == "user" for message in session.get("messages", [])):
                completed_speaking_sessions += 1
                stamp = session.get("updated_at")
                try:
                    parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00")) if isinstance(stamp, str) else stamp
                    if parsed and parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=timezone.utc)
                    if parsed:
                        active_dates.add(parsed.astimezone().date())
                except (ValueError, TypeError, AttributeError):
                    pass

        for completion in listening_completions:
            stamp = completion.get("completed_at")
            try:
                parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00")) if isinstance(stamp, str) else stamp
                if parsed and parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                if parsed:
                    active_dates.add(parsed.astimezone().date())
            except (ValueError, TypeError, AttributeError):
                continue

        streak = 0
        date_cursor = today if today in active_dates else today - timedelta(days=1)
        while date_cursor in active_dates:
            streak += 1
            date_cursor -= timedelta(days=1)

        recent_docs = await db.materials.find({"is_seeded": {"$ne": True}}).sort("created_at", -1).limit(5).to_list(length=5)
        recent_materials = []
        for doc in recent_docs:
            doc["id"] = str(doc.get("_id", doc.get("id", "")))
            recent_materials.append(MaterialResponse(**doc))

        actual_vocab = {"user_id": "default", "is_seeded": False}
        vocab_saved_count = await db.vocabulary.count_documents(actual_vocab)
        vocab_mastered_count = await db.vocabulary.count_documents({**actual_vocab, "status": "mastered"})
        vocab_due_query = {**actual_vocab, "due_for_revision": True}
        vocab_due_count = await db.vocabulary.count_documents(vocab_due_query)
        vocab_docs = await db.vocabulary.find(vocab_due_query).sort("created_at", -1).limit(6).to_list(length=6)
        vocab_queue = []
        for doc in vocab_docs:
            doc["id"] = str(doc.get("_id", doc.get("id", "")))
            vocab_queue.append(VocabularyResponse(**doc))
        progress = await db.progress.find_one({"user_id": "default", "is_seeded": False})
        completed_lessons = set(progress.get("completed_lessons", [])) if progress else set()
        curriculum_by_level = {
            "A1": A1_LESSONS,
            "A2": A2_LESSONS,
            "B1": B1_LESSONS,
        }
        level_progress = {
            level: {
                "completed": sum(lesson["id"] in completed_lessons for lesson in lessons),
                "total": len(lessons),
            }
            for level, lessons in curriculum_by_level.items()
        }

        skill_scores = {
            key: round(sum(values) / len(values)) if values else None
            for key, values in score_buckets.items()
        }
        return DashboardSummaryResponse(
            learner_name=user.get("name", "Learner") if user else "Learner",
            current_level=user.get("current_level", "A1") if user else "A1",
            target_level=user.get("target_level", "") if user else "",
            daily_stats=DailyStats(
                streak_days=streak,
                today_minutes=today_seconds // 60,
                goal_minutes=user.get("daily_goal_minutes") if user else None,
                completed_today=len(today_attempts),
                total_exercises=len(attempts),
            ),
            skill_scores=SkillScores(**skill_scores),
            recent_materials=recent_materials,
            weak_topics=[],
            vocab_due_count=vocab_due_count,
            vocab_saved_count=vocab_saved_count,
            vocab_mastered_count=vocab_mastered_count,
            completed_lessons_count=len(progress.get("completed_lessons", [])) if progress else 0,
            level_progress=level_progress,
            speaking_sessions_count=completed_speaking_sessions,
            listening_resources_completed=len(listening_completions),
            vocab_queue=vocab_queue,
        )

    @staticmethod
    async def update_learner_level(new_level: str) -> dict:
        valid_levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
        if new_level not in valid_levels:
            raise ValueError(f"Invalid CEFR level: {new_level}. Must be one of {valid_levels}")
        db = get_db()
        existing = await db.users.find_one({"username": "learner"})
        updates = {"$set": {"username": "learner", "current_level": new_level, "is_seeded": False}}
        if existing and existing.get("is_seeded"):
            updates["$unset"] = {
                "name": "", "target_level": "", "streak_days": "", "daily_goal_minutes": "",
                "native_language": "", "created_at": ""
            }
        await db.users.update_one({"username": "learner"}, updates, upsert=True)
        return {"success": True, "current_level": new_level}
