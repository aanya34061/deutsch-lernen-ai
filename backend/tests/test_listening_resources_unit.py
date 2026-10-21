import pytest
from httpx import ASGITransport, AsyncClient

from app.data.practice_listening_data import STARTING_LISTENING_EXERCISES
from app.data.listening_resources import LISTENING_RESOURCE_CATALOG
from app.main import app
from app.services.practice_service import PracticeService


class Cursor:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, *_args):
        return self

    async def to_list(self, length):
        return self.docs[:length]


class Collection:
    def __init__(self, docs=None):
        self.docs = list(docs or [])

    def find(self, query):
        docs = [doc for doc in self.docs if doc.get("user_id") == query.get("user_id")]
        resource_ids = query.get("resource_id", {}).get("$in")
        if resource_ids is not None:
            docs = [doc for doc in docs if doc.get("resource_id") in resource_ids]
        return Cursor(docs)

    async def find_one(self, query):
        return next((doc for doc in self.docs if all(doc.get(k) == v for k, v in query.items())), None)

    async def update_one(self, query, update, upsert=False):
        doc = await self.find_one(query)
        if doc is None and upsert:
            self.docs.append(dict(update["$setOnInsert"]))


class Database:
    def __init__(self, completions=None, attempts=None):
        self.listening_resource_completions = Collection(completions)
        self.exercise_attempts = Collection(attempts)
        self.practice_listening = Collection(STARTING_LISTENING_EXERCISES)


@pytest.mark.asyncio
async def test_resource_catalog_filters_and_joins_only_saved_completion(monkeypatch):
    resource = next(item for item in LISTENING_RESOURCE_CATALOG if item["cefr_level"] == "A1")
    db = Database(completions=[{
        "user_id": "default", "resource_id": resource["id"],
        "cefr_level": "A1", "completed_at": "2026-01-01T00:00:00+00:00",
    }])
    monkeypatch.setattr("app.services.practice_service.get_db", lambda: db)

    a1 = await PracticeService.list_listening_resources("A1")
    dialogues = await PracticeService.list_listening_resources("B1", category="Everyday Conversations")

    assert a1 and all(item["cefr_level"] == "A1" for item in a1)
    assert next(item for item in a1 if item["id"] == resource["id"])["completed_at"] == "2026-01-01T00:00:00+00:00"
    assert dialogues and all("Everyday Conversations" in item["categories"] for item in dialogues)
    assert all(item["completed_at"] is None for item in dialogues)


@pytest.mark.asyncio
async def test_manual_completion_is_persisted_and_idempotent(monkeypatch):
    db = Database()
    monkeypatch.setattr("app.services.practice_service.get_db", lambda: db)
    resource_id = LISTENING_RESOURCE_CATALOG[0]["id"]

    first = await PracticeService.complete_listening_resource(resource_id)
    second = await PracticeService.complete_listening_resource(resource_id)

    assert first == second
    assert len(db.listening_resource_completions.docs) == 1
    assert db.listening_resource_completions.docs[0]["cefr_level"] == "A1"


@pytest.mark.asyncio
async def test_external_completion_counts_as_listening_activity_without_score(monkeypatch):
    db = Database(completions=[{
        "user_id": "default", "resource_id": "goethe-a1-model-listening",
        "cefr_level": "A1", "completed_at": "2026-01-01T00:00:00+00:00",
    }])
    monkeypatch.setattr("app.services.practice_service.get_db", lambda: db)

    progress = await PracticeService.get_practice_progress()

    assert progress.listening.completed_count == 1
    assert progress.listening.average_score is None
    assert progress.cefr_breakdown["A1"] == 1
    assert progress.total_completed == 1
    assert progress.recent_activity[0]["completed"] is True


@pytest.mark.asyncio
async def test_resource_api_filters_and_persists_completion(monkeypatch):
    db = Database()
    monkeypatch.setattr("app.services.practice_service.get_db", lambda: db)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        listing = await client.get("/api/v1/practice/listening/resources?level=A2&category=Listening%20Practice")
        invalid = await client.get("/api/v1/practice/listening/resources?level=C1")
        complete = await client.post("/api/v1/practice/listening/resources/goethe-a2-model-listening/complete")
        refreshed = await client.get("/api/v1/practice/listening/resources?level=A2")

    assert listing.status_code == 200 and listing.json()
    assert all(item["cefr_level"] == "A2" for item in listing.json())
    assert invalid.status_code == 422
    assert complete.status_code == 200
    saved = next(item for item in refreshed.json() if item["id"] == "goethe-a2-model-listening")
    assert saved["completed_at"] == complete.json()["completed_at"]


@pytest.mark.asyncio
async def test_authored_listening_detail_exposes_only_tts_utterance_not_transcript_or_answers(monkeypatch):
    monkeypatch.setattr("app.services.practice_service.get_db", lambda: Database())

    exercise = await PracticeService.get_listening_exercise("listen-a1-1")

    assert exercise.audio_text.startswith("Verkäufer:")
    assert not hasattr(exercise, "script_de")
    assert not hasattr(exercise, "translation_en")
    assert all("correct_answer" not in question for question in exercise.questions)


def test_catalog_has_verified_fields_and_nonempty_levels():
    assert all(item["source_url"].startswith("https://") for item in LISTENING_RESOURCE_CATALOG)
    assert {item["cefr_level"] for item in LISTENING_RESOURCE_CATALOG} == {"A1", "A2", "B1"}
    assert all(item["title"] and item["publisher"] and item["categories"] for item in LISTENING_RESOURCE_CATALOG)
