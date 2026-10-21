import pytest
from httpx import AsyncClient, ASGITransport
from pydantic import ValidationError

from app.data.practice_reading_data import STARTING_READING_EXERCISES
from app.main import app
from app.models.practice import ReadingSubmissionRequest
from app.services.practice_service import PracticeService


class FakeCursor:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, *_args):
        return self

    async def to_list(self, length):
        return self.docs[:length]


class FakeCollection:
    def __init__(self, docs=None):
        self.docs = docs or []
        self.inserted = []

    def find(self, query):
        docs = self.docs
        if "cefr_level" in query:
            docs = [doc for doc in docs if doc.get("cefr_level") == query["cefr_level"]]
        if "topic" in query:
            docs = [doc for doc in docs if doc.get("topic", "").lower() == query["topic"]["$regex"].strip("^").strip("$").lower()]
        return FakeCursor(docs)

    async def find_one(self, query):
        if "id" in query:
            return next((doc for doc in self.docs if doc.get("id") == query["id"]), None)
        return None

    async def insert_one(self, document):
        self.inserted.append(document)

    async def update_one(self, *_args, **_kwargs):
        return None


class FakeDatabase:
    def __init__(self):
        self.practice_reading = FakeCollection(STARTING_READING_EXERCISES)
        self.exercise_attempts = FakeCollection()
        self.progress = FakeCollection()
        self.users = FakeCollection()


@pytest.mark.asyncio
async def test_reading_service_hides_answers_scores_and_persists(monkeypatch):
    database = FakeDatabase()
    monkeypatch.setattr("app.services.practice_service.get_db", lambda: database)

    listing = await PracticeService.list_reading_exercises("A1")
    assert len(listing) >= 3
    assert all(row["is_seeded"] for row in listing)
    detail = await PracticeService.get_reading_exercise("read-a1-3")
    assert all("correct_answer" not in question for question in detail.questions)

    result = await PracticeService.evaluate_reading_submission(
        "read-a1-3", {"q3": "Rund um die Uhr"}
    )
    assert result.score == 33
    assert result.results[-1].is_correct
    assert len(database.exercise_attempts.inserted) == 1
    assert database.exercise_attempts.inserted[0]["score"] == result.score
    assert database.exercise_attempts.inserted[0]["user_id"] == "default"
    assert database.exercise_attempts.inserted[0]["is_seeded"] is False


def test_reading_submission_request_rejects_malformed_answers():
    with pytest.raises(ValidationError):
        ReadingSubmissionRequest(answers={"q1": {"unexpected": "object"}})
    with pytest.raises(ValidationError):
        ReadingSubmissionRequest(answers={}, time_spent_seconds=-1)


@pytest.mark.asyncio
async def test_reading_api_retrieval_validation_and_saved_result(monkeypatch):
    database = FakeDatabase()
    monkeypatch.setattr("app.services.practice_service.get_db", lambda: database)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/practice/reading?level=A1")
        assert response.status_code == 200
        exercise_id = response.json()[0]["id"]

        detail = await client.get(f"/api/v1/practice/reading/{exercise_id}")
        assert detail.status_code == 200
        assert all("correct_answer" not in question for question in detail.json()["questions"])

        invalid = await client.post(f"/api/v1/practice/reading/{exercise_id}/submit", json={
            "answers": {"q1": "not an available option"}
        })
        assert invalid.status_code == 422

        exercise_id = "read-a1-3"
        submitted = await client.post(f"/api/v1/practice/reading/{exercise_id}/submit", json={
            "answers": {"q3": "rund um die Uhr"}
        })
        assert submitted.status_code == 200
        assert submitted.json()["score"] == 33
        assert database.exercise_attempts.inserted[-1]["exercise_id"] == exercise_id
        assert database.exercise_attempts.inserted[-1]["score"] == submitted.json()["score"]


def test_starter_reading_content_meets_level_and_question_requirements():
    counts = {level: sum(item["cefr_level"] == level for item in STARTING_READING_EXERCISES) for level in ("A1", "A2", "B1")}
    assert counts == {"A1": 3, "A2": 2, "B1": 2}
    assert all(question.get("explanation_en") for item in STARTING_READING_EXERCISES for question in item["questions"])
    assert any(question["type"] == "short_answer" for item in STARTING_READING_EXERCISES for question in item["questions"])
