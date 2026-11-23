from app.data.curriculum_manifest import get_curriculum_manifest
from app.database import get_db, seed_initial_data_if_empty
from collections import Counter


def test_a1_manifest_has_six_modules_and_complete_published_lessons():
    manifest = get_curriculum_manifest()
    modules = [module for module in manifest["modules"] if module["level"] == "A1"]
    topics = [topic for topic in manifest["topics"] if topic["level"] == "A1"]
    lessons = [lesson for lesson in manifest["lessons"] if lesson["cefr_level"] == "A1"]
    assert len(modules) == 6
    assert len(topics) == len(lessons) == 28
    assert len({module["module_id"] for module in modules}) == 6
    assert len({topic["topic_id"] for topic in topics}) == 28
    assert len({lesson["lesson_id"] for lesson in lessons}) == 28
    assert all(module["topic_ids"] for module in modules)
    for lesson in lessons:
        assert lesson["publication_status"] == "published"
        assert len(lesson["objectives"]) >= 3
        assert len(lesson["explanation_en"]) >= 250
        assert len(lesson["examples"]) >= 3
        assert len(lesson["vocabulary"]) >= 3
        assert lesson["summary_en"]
        assert len(lesson["exercises"]) >= 3
        assert all(exercise.get("correct_answer") is not None and exercise.get("explanation_en") for exercise in lesson["exercises"])


def test_a2_manifest_has_five_modules_and_complete_published_lessons():
    manifest = get_curriculum_manifest()
    modules = [module for module in manifest["modules"] if module["level"] == "A2"]
    topics = [topic for topic in manifest["topics"] if topic["level"] == "A2"]
    lessons = [lesson for lesson in manifest["lessons"] if lesson["cefr_level"] == "A2"]
    assert len(modules) == 5
    assert len(topics) == len(lessons) == 31
    assert len({module["module_id"] for module in modules}) == 5
    assert len({topic["topic_id"] for topic in topics}) == 31
    assert len({lesson["lesson_id"] for lesson in lessons}) == 31
    assert all(module["topic_ids"] for module in modules)
    for lesson in lessons:
        assert lesson["publication_status"] == "published"
        assert len(lesson["explanation_en"]) >= 250
        assert len(lesson["examples"]) >= 3 and len(lesson["vocabulary"]) >= 3
        assert len(lesson["exercises"]) >= 3
        assert all(exercise.get("correct_answer") is not None and exercise.get("explanation_en") for exercise in lesson["exercises"])


def test_complete_curriculum_manifest_has_expected_structure_and_no_placeholders():
    manifest = get_curriculum_manifest()
    expected = {"A1": (6, 28), "A2": (5, 31), "B1": (7, 28)}
    assert len(manifest["modules"]) == 18
    assert len(manifest["topics"]) == len(manifest["lessons"]) == 87
    for level, (module_count, topic_count) in expected.items():
        modules = [module for module in manifest["modules"] if module["level"] == level]
        topics = [topic for topic in manifest["topics"] if topic["level"] == level]
        lessons = [lesson for lesson in manifest["lessons"] if lesson["cefr_level"] == level]
        assert len(modules) == module_count
        assert len(topics) == len(lessons) == topic_count
        assert len({module["module_id"] for module in modules}) == module_count
        assert len({topic["topic_id"] for topic in topics}) == topic_count
        assert len({lesson["lesson_id"] for lesson in lessons}) == topic_count
        assert all(module["topic_ids"] for module in modules)
        for lesson in lessons:
            assert lesson["publication_status"] == "published"
            assert len(lesson["explanation_en"]) >= 250
            assert len(lesson["examples"]) >= 3 and len(lesson["vocabulary"]) >= 3
            assert lesson["summary_en"] and len(lesson["exercises"]) >= 3
            assert all(exercise.get("correct_answer") is not None and exercise.get("explanation_en") for exercise in lesson["exercises"])


def test_curriculum_answer_keys_match_authored_choice_tokens():
    manifest = get_curriculum_manifest()
    for lesson in manifest["lessons"]:
        for exercise in lesson["exercises"]:
            answer = exercise.get("correct_answer")
            options = exercise.get("options") or []
            if exercise.get("type") == "sentence_order":
                assert Counter(str(answer).split()) == Counter(" ".join(map(str, options)).split()), exercise["id"]
            elif exercise.get("type") in {"multiple_choice", "true_false"}:
                assert answer in options, exercise["id"]


async def test_a1_seed_is_idempotent_and_preserves_learner_progress():
    db = get_db()
    await db.progress.insert_one({"user_id": "default", "is_seeded": False, "completed_lessons": ["a1-lesson-1"]})
    await seed_initial_data_if_empty()
    await seed_initial_data_if_empty()
    assert await db.curriculum_modules.count_documents({"level": "A1"}) == 6
    assert await db.curriculum_topics.count_documents({"level": "A1"}) == 28
    assert await db.curriculum_lessons.count_documents({"cefr_level": "A1"}) == 28
    progress = await db.progress.find_one({"user_id": "default", "is_seeded": False})
    assert progress["completed_lessons"] == ["a1-lesson-1"]


async def test_seed_persists_all_levels_idempotently():
    db = get_db()
    await seed_initial_data_if_empty()
    await seed_initial_data_if_empty()
    for level, modules, topics, lessons in (("A1", 6, 28, 28), ("A2", 5, 31, 31), ("B1", 7, 28, 28)):
        assert await db.curriculum_modules.count_documents({"level": level}) == modules
        assert await db.curriculum_topics.count_documents({"level": level}) == topics
        assert await db.curriculum_lessons.count_documents({"cefr_level": level}) == lessons


async def test_a1_modules_topics_and_lesson_content_are_served_from_database(client):
    modules = await client.get("/api/v1/lessons/modules?level=A1")
    assert modules.status_code == 200
    result = modules.json()
    assert len(result) == 6
    assert sum(len(module["topics"]) for module in result) == 28
    assert all(topic["lesson_id"] for module in result for topic in module["topics"])

    lessons = await client.get("/api/v1/lessons?level=A1")
    assert lessons.status_code == 200
    assert len(lessons.json()) == 28
    lesson_id = result[0]["topics"][0]["lesson_id"]
    detail = await client.get(f"/api/v1/lessons/{lesson_id}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["publication_status"] == "published"
    assert body["explanation_en"]
    assert body["examples"] and body["vocabulary"] and body["exercises"]
    assert "correct_answer" not in body["exercises"][0]


async def test_a2_modules_and_lessons_are_served_from_database(client):
    modules = await client.get("/api/v1/lessons/modules?level=A2")
    lessons = await client.get("/api/v1/lessons?level=A2")
    assert modules.status_code == lessons.status_code == 200
    assert len(modules.json()) == 5
    assert sum(len(module["topics"]) for module in modules.json()) == 31
    assert len(lessons.json()) == 31


async def test_b1_modules_and_lessons_are_served_from_database(client):
    modules = await client.get("/api/v1/lessons/modules?level=B1")
    lessons = await client.get("/api/v1/lessons?level=B1")
    assert modules.status_code == lessons.status_code == 200
    assert len(modules.json()) == 7
    assert sum(len(module["topics"]) for module in modules.json()) == 28
    assert len(lessons.json()) == 28
