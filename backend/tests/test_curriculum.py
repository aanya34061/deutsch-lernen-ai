import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_list_lessons_and_filtering(client: AsyncClient):
    # All lessons
    res = await client.get("/api/v1/lessons")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 8  # A1, A2, B1 lessons

    # Filter A1
    res_a1 = await client.get("/api/v1/lessons?level=A1")
    assert res_a1.status_code == 200
    a1_data = res_a1.json()
    assert all(l["cefr_level"] == "A1" for l in a1_data)
    assert len(a1_data) >= 4

    # Filter A2
    res_a2 = await client.get("/api/v1/lessons?level=A2")
    assert res_a2.status_code == 200
    a2_data = res_a2.json()
    assert all(l["cefr_level"] == "A2" for l in a2_data)
    assert len(a2_data) >= 2

    # Filter B1
    res_b1 = await client.get("/api/v1/lessons?level=B1")
    assert res_b1.status_code == 200
    b1_data = res_b1.json()
    assert all(l["cefr_level"] == "B1" for l in b1_data)
    assert len(b1_data) >= 2

@pytest.mark.asyncio
async def test_get_lesson_detail(client: AsyncClient):
    res = await client.get("/api/v1/lessons/a1-lesson-1")
    assert res.status_code == 200
    lesson = res.json()
    assert lesson["id"] == "a1-lesson-1"
    assert lesson["cefr_level"] == "A1"
    assert len(lesson["objectives"]) > 0
    assert len(lesson["grammar_rules"]) > 0
    assert len(lesson["vocabulary"]) > 0
    assert len(lesson["exercises"]) > 0

@pytest.mark.asyncio
async def test_mark_lesson_completed(client: AsyncClient):
    res = await client.post("/api/v1/lessons/a1-lesson-1/complete")
    assert res.status_code == 200
    assert res.json()["is_completed"] is True

    # Check in list
    list_res = await client.get("/api/v1/lessons?level=A1")
    l1 = next((l for l in list_res.json() if l["id"] == "a1-lesson-1"), None)
    assert l1 is not None
    assert l1["is_completed"] is True

@pytest.mark.asyncio
async def test_exercise_learner_view_and_submissions(client: AsyncClient):
    # 1. Learner view doesn't disclose correct answer
    res_view = await client.get("/api/v1/exercises/a1-l1-ex1")
    assert res_view.status_code == 200
    view = res_view.json()
    assert "correct_answer" not in view
    assert "explanation_en" not in view

    # 2. Submit correct answer
    sub_correct = await client.post("/api/v1/exercises/a1-l1-ex1/submit", json={"user_answer": "bin"})
    assert sub_correct.status_code == 200
    result = sub_correct.json()
    assert result["is_correct"] is True
    assert result["score"] == 100
    assert "bin" in result["explanation_en"]

    # 3. Submit wrong answer
    sub_wrong = await client.post("/api/v1/exercises/a1-l1-ex1/submit", json={"user_answer": "sind"})
    assert sub_wrong.status_code == 200
    result_wrong = sub_wrong.json()
    assert result_wrong["is_correct"] is False
    assert result_wrong["score"] == 0
    assert result_wrong["correct_answer"] == "bin"

@pytest.mark.asyncio
async def test_sentence_order_exercise_alternatives(client: AsyncClient):
    # Submit valid sentence order as array
    sub = await client.post(
        "/api/v1/exercises/a1-l1-ex3/submit",
        json={"user_answer": ["Guten", "Tag", "Ich", "heiße", "Laura"]}
    )
    assert sub.status_code == 200
    assert sub.json()["is_correct"] is True
