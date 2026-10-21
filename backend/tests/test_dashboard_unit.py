import pytest

from app.services.dashboard_service import DashboardService


@pytest.fixture(autouse=True)
async def setup_db():
    # Override the integration fixture so these tests never connect to or mutate
    # the developer's configured MongoDB database.
    yield


class FakeCursor:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, *_args):
        return self

    def limit(self, count):
        self.docs = self.docs[:count]
        return self

    async def to_list(self, length):
        return self.docs[:length]


class FakeCollection:
    def __init__(self, docs=()):
        self.docs = list(docs)
        self.inserted = []

    @staticmethod
    def _matches(doc, query):
        for key, expected in query.items():
            actual = doc.get(key)
            if isinstance(expected, dict) and "$ne" in expected:
                if actual == expected["$ne"]:
                    return False
            elif actual != expected:
                return False
        return True

    async def find_one(self, query):
        return next((d for d in self.docs if self._matches(d, query)), None)

    def find(self, query):
        return FakeCursor([d.copy() for d in self.docs if self._matches(d, query)])

    async def count_documents(self, query):
        return sum(self._matches(d, query) for d in self.docs)

    async def insert_one(self, document):
        self.inserted.append(document.copy())

    async def update_one(self, query, update, upsert=False):
        doc = next((d for d in self.docs if self._matches(d, query)), None)
        if doc is None and upsert:
            doc = {key: value for key, value in query.items() if not isinstance(value, dict)}
            self.docs.append(doc)
        if doc is None:
            return
        for field, value in update.get("$set", {}).items():
            doc[field] = value
        for field, value in update.get("$addToSet", {}).items():
            values = doc.setdefault(field, [])
            if value not in values:
                values.append(value)


class FakeDatabase:
    def __init__(self, *, attempts=(), progress=(), vocabulary=(), users=(), speaking_sessions=(), listening_completions=()):
        self.exercise_attempts = FakeCollection(attempts)
        self.progress = FakeCollection(progress)
        self.vocabulary = FakeCollection(vocabulary)
        self.users = FakeCollection(users)
        self.materials = FakeCollection()
        self.speaking_sessions = FakeCollection(speaking_sessions)
        self.listening_resource_completions = FakeCollection(listening_completions)


@pytest.mark.asyncio
async def test_dashboard_uses_only_default_learners_persisted_records(monkeypatch):
    database = FakeDatabase(
        users=[{"username": "learner", "current_level": "A2", "is_seeded": False}],
        progress=[
            {"user_id": "legacy-demo", "is_seeded": True, "completed_lessons": ["a1-lesson-1", "a1-lesson-2"]},
            {"user_id": "default", "completed_lessons": ["a1-lesson-1", "a1-lesson-2", "a1-lesson-3"]},
            {"user_id": "default", "is_seeded": False, "completed_lessons": ["a1-lesson-1"]},
        ],
        attempts=[
            {"user_id": "legacy-demo", "is_seeded": True, "skill": "reading", "score": 100, "timestamp": "2026-10-21T12:00:00+00:00"},
            {"user_id": "default", "skill": "reading", "score": 99, "timestamp": "2026-10-21T12:00:00+00:00"},
            {"user_id": "default", "is_seeded": False, "skill": "reading", "score": 40, "timestamp": "2026-10-21T12:00:00+00:00"},
        ],
        vocabulary=[
            {"user_id": "legacy-demo", "is_seeded": True, "status": "mastered"},
            {"user_id": "default", "status": "mastered"},
            {"user_id": "default", "is_seeded": False, "status": "new"},
        ],
        speaking_sessions=[
            {"user_id": "default", "is_seeded": False, "messages": [{"role": "assistant"}]},
            {"user_id": "default", "messages": [{"role": "user"}, {"role": "assistant"}]},
            {"user_id": "default", "is_seeded": False, "messages": [{"role": "user"}, {"role": "assistant"}]},
            {"user_id": "legacy-demo", "is_seeded": False, "messages": [{"role": "user"}]},
        ],
        listening_completions=[{"user_id": "default", "resource_id": "goethe-a1-model-listening", "cefr_level": "A1", "completed_at": "2026-10-21T12:00:00+00:00"}],
    )
    monkeypatch.setattr("app.services.dashboard_service.get_db", lambda: database)

    result = await DashboardService.get_dashboard_summary()

    assert result.current_level == "A2"
    assert result.daily_stats.total_exercises == 1
    assert result.skill_scores.reading == 40
    assert result.completed_lessons_count == 1
    assert result.vocab_saved_count == 1
    assert result.vocab_mastered_count == 0
    assert result.level_progress["A1"].completed == 1
    assert result.speaking_sessions_count == 1
    assert result.listening_resources_completed == 1


@pytest.mark.asyncio
async def test_dashboard_empty_state_has_no_activity_or_scores(monkeypatch):
    monkeypatch.setattr("app.services.dashboard_service.get_db", lambda: FakeDatabase())

    result = await DashboardService.get_dashboard_summary()

    assert result.daily_stats.total_exercises == 0
    assert result.daily_stats.streak_days == 0
    assert result.completed_lessons_count == 0
    assert result.skill_scores.reading is None
    assert result.vocab_saved_count == 0
    assert result.listening_resources_completed == 0
    assert all(progress.completed == 0 for progress in result.level_progress.values())


@pytest.mark.asyncio
async def test_lesson_completion_is_scoped_and_idempotent(monkeypatch):
    from app.services.curriculum_service import CurriculumService

    database = FakeDatabase(progress=[{"user_id": "legacy-demo", "completed_lessons": ["a1-lesson-2"]}])
    monkeypatch.setattr("app.services.curriculum_service.get_db", lambda: database)

    assert await CurriculumService.mark_lesson_completed("a1-lesson-1") is True
    assert await CurriculumService.mark_lesson_completed("a1-lesson-1") is True
    completed = await CurriculumService.get_user_completed_lesson_ids()

    assert completed == {"a1-lesson-1"}
    own_progress = next(doc for doc in database.progress.docs if doc.get("user_id") == "default")
    assert own_progress["completed_lessons"] == ["a1-lesson-1"]
    assert own_progress["is_seeded"] is False


@pytest.mark.asyncio
async def test_exercise_attempt_persists_real_score_under_default_user(monkeypatch):
    from app.services.exercise_service import ExerciseService

    database = FakeDatabase()
    monkeypatch.setattr("app.services.exercise_service.get_db", lambda: database)

    result = await ExerciseService.evaluate_submission("a1-l1-ex1", "bin")

    assert result.score == 100
    assert len(database.exercise_attempts.inserted) == 1
    attempt = database.exercise_attempts.inserted[0]
    assert attempt["user_id"] == "default"
    assert attempt["is_seeded"] is False
