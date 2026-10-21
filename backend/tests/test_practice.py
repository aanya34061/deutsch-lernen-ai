import pytest
from unittest.mock import patch, AsyncMock
from app.database import get_db
from app.services.practice_service import PracticeService
from app.services.ollama_service import OllamaService

@pytest.mark.asyncio
async def test_reading_list_and_get(client):
    """Verify listing and retrieving reading exercises with question hiding."""
    res = await client.get("/api/v1/practice/reading?level=A1")
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 1
    first_id = items[0]["id"]

    # Get single exercise (learner view)
    get_res = await client.get(f"/api/v1/practice/reading/{first_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["id"] == first_id
    assert "passage_de" in data
    assert len(data["questions"]) > 0
    # Crucial security requirement: correct_answer must NOT be leaked in learner view!
    for q in data["questions"]:
        assert "correct_answer" not in q
        assert "question" in q

@pytest.mark.asyncio
async def test_reading_submission_evaluation(client):
    """Verify reading answers evaluation, scoring, and translation reveal."""
    # Submit answers for read-a1-1 (Im Café am Marktplatz)
    submission_payload = {
        "answers": {
            "q1": "Kaffee mit Milch und Zucker",
            "q2": "False",
            "q3": "6 Euro 50"
        },
        "time_spent_seconds": 90
    }
    sub_res = await client.post("/api/v1/practice/reading/read-a1-1/submit", json=submission_payload)
    assert sub_res.status_code == 200
    data = sub_res.json()
    assert data["exercise_id"] == "read-a1-1"
    assert data["score"] == 100
    assert data["is_perfect"] is True
    assert len(data["results"]) == 3
    for r in data["results"]:
        assert r["is_correct"] is True
    # Translation revealed after attempt
    assert "translation_en" in data
    assert "Waiter:" in data["translation_en"]

@pytest.mark.asyncio
async def test_reading_starter_catalog_alternatives_validation_and_persistence(client):
    for level, minimum in (("A1", 3), ("A2", 2), ("B1", 2)):
        response = await client.get(f"/api/v1/practice/reading?level={level}")
        assert response.status_code == 200
        assert len(response.json()) >= minimum
        assert all(item["is_seeded"] for item in response.json())

    detail = (await client.get("/api/v1/practice/reading/read-a1-3")).json()
    assert any(question["type"] == "short_answer" for question in detail["questions"])
    assert all("correct_answer" not in question for question in detail["questions"])

    bad_choice = await client.post("/api/v1/practice/reading/read-a1-1/submit", json={
        "answers": {"q1": "A choice that is not listed"}
    })
    assert bad_choice.status_code == 422

    accepted = await client.post("/api/v1/practice/reading/read-a1-3/submit", json={
        "answers": {"q3": "Rund um die Uhr"}
    })
    assert accepted.status_code == 200
    result = next(row for row in accepted.json()["results"] if row["question_id"] == "q3")
    assert result["is_correct"] is True

    from app.database import get_db
    attempts = await get_db().exercise_attempts.find({"exercise_id": "read-a1-3", "skill": "reading"}).to_list(length=100)
    assert any(attempt["score"] == accepted.json()["score"] for attempt in attempts)

@pytest.mark.asyncio
async def test_reading_topic_filter_and_bad_submission(client):
    response = await client.get("/api/v1/practice/reading?level=A1&topic=Food%2C%20Drinks%20%26%20Ordering")
    assert response.status_code == 200
    assert response.json()
    assert all(item["topic"] == "Food, Drinks & Ordering" for item in response.json())

    malformed = await client.post("/api/v1/practice/reading/read-a1-1/submit", json={"answers": {"missing": "answer"}})
    assert malformed.status_code == 422

@pytest.mark.asyncio
async def test_listening_list_and_submission(client):
    """Verify listening exercise retrieval and evaluation."""
    res = await client.get("/api/v1/practice/listening?level=A1")
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 1
    first_id = items[0]["id"]

    # Get learner view (script and translation must be hidden)
    get_res = await client.get(f"/api/v1/practice/listening/{first_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert "script_de" not in data or data.get("script_de") is None
    assert "translation_en" not in data or data.get("translation_en") is None

    # Submit answers
    sub_payload = {
        "answers": {
            "lq1": "Äpfel und Erdbeeren",
            "lq2": "Die süßen roten",
            "lq3": "4,80 Euro"
        },
        "time_spent_seconds": 60
    }
    sub_res = await client.post("/api/v1/practice/listening/listen-a1-1/submit", json=sub_payload)
    assert sub_res.status_code == 200
    result_data = sub_res.json()
    assert result_data["score"] == 100
    # Script & translation revealed upon submission
    assert "script_de" in result_data
    assert "Verkäufer:" in result_data["script_de"]

@pytest.mark.asyncio
async def test_writing_draft_persistence(client):
    """Verify saving, retrieving, and deleting a writing draft."""
    prompt_id = "write-a1-1"
    draft_content = "Hallo! Ich heiße Lukas und ich wohne in..."

    # Save draft
    save_res = await client.post("/api/v1/practice/writing/drafts", json={
        "prompt_id": prompt_id,
        "content": draft_content
    })
    assert save_res.status_code == 200
    draft_data = save_res.json()
    assert draft_data["prompt_id"] == prompt_id
    assert draft_data["content"] == draft_content
    draft_id = draft_data["id"]

    # Retrieve draft
    get_res = await client.get(f"/api/v1/practice/writing/drafts/{prompt_id}")
    assert get_res.status_code == 200
    assert get_res.json()["content"] == draft_content

    # Delete draft
    del_res = await client.delete(f"/api/v1/practice/writing/drafts/{draft_id}")
    assert del_res.status_code == 200

@pytest.mark.asyncio
async def test_writing_evaluation_with_mocked_ai(client):
    """Verify writing evaluation with mocked Ollama AI response."""
    mock_ai_json = (
        '{\n'
        '  "corrected_text": "Hallo! Ich heiße Anna. Ich wohne in Berlin.",\n'
        '  "grammar_mistakes": [],\n'
        '  "word_order_mistakes": [],\n'
        '  "article_mistakes": [],\n'
        '  "spelling_mistakes": ["\'berlin\' should be capitalized as \'Berlin\'."],\n'
        '  "explanation_en": "Very good introduction! Just remember to capitalize city names.",\n'
        '  "natural_alternative_de": "Hallo! Mein Name ist Anna und ich lebe in Berlin.",\n'
        '  "suggestions": ["Keep up the great work!"],\n'
        '  "score": 92\n'
        '}'
    )

    with patch.object(
        OllamaService,
        "check_status",
        new=AsyncMock(return_value={"status": "ready", "is_ready": True})
    ), patch.object(
        OllamaService,
        "generate_chat",
        new=AsyncMock(return_value=mock_ai_json)
    ):
        eval_res = await client.post("/api/v1/practice/writing/evaluate", json={
            "prompt_id": "write-a1-1",
            "content": "Hallo! Ich heiße Anna. Ich wohne in berlin.",
            "cefr_level": "A1"
        })
        assert eval_res.status_code == 200
        data = eval_res.json()
        assert data["score"] == 92
        assert data["is_ai_evaluated"] is True
        assert data["evaluation_source"] == "ollama"
        assert "Berlin" in data["corrected_text"]
        assert len(data["spelling_mistakes"]) > 0

@pytest.mark.asyncio
async def test_writing_evaluation_fallback_when_ollama_offline(client):
    """Verify deterministic rule-based evaluation when Ollama is offline."""
    with patch.object(
        OllamaService,
        "check_status",
        new=AsyncMock(return_value={"status": "ollama_not_running", "is_ready": False})
    ):
        eval_res = await client.post("/api/v1/practice/writing/evaluate", json={
            "prompt_id": "write-a1-1",
            "content": "ich esse einen apfel in der schule.",
            "cefr_level": "A1"
        })
        assert eval_res.status_code == 200
        data = eval_res.json()
        assert data["is_ai_evaluated"] is False
        assert data["evaluation_source"] == "deterministic_rules"
        # Deterministic check flags lowercase nouns: 'apfel' and 'schule'
        assert any("Apfel" in m for m in data["spelling_mistakes"])

@pytest.mark.asyncio
async def test_speaking_session_lifecycle(client):
    """When local AI is unavailable, keep the authored greeting and do not invent a tutor turn."""
    # 1. Start speaking session
    start_res = await client.post("/api/v1/practice/speaking/sessions", json={
        "scenario_id": "speak-a1-1",
        "cefr_level": "A1"
    })
    assert start_res.status_code == 200
    start_data = start_res.json()
    session_id = start_data["session_id"]
    assert "Café" in start_data["text_de"]
    assert start_data["turn_count"] == 1

    # 2. With no AI response, the user's turn must not be reported as saved.
    with patch.object(OllamaService, "check_status", new=AsyncMock(return_value={"is_ready": False})):
        msg_res = await client.post(f"/api/v1/practice/speaking/sessions/{session_id}/message", json={
            "message": "Ich möchte bitte einen Kaffee und ein Croissant."
        })
    assert msg_res.status_code == 503

    # 3. Retrieve conversation history
    get_res = await client.get(f"/api/v1/practice/speaking/sessions/{session_id}")
    assert get_res.status_code == 200
    session_data = get_res.json()
    # Only the persisted authored greeting remains; the failed AI turn is not stored.
    assert len(session_data["messages"]) == 1

@pytest.mark.asyncio
async def test_practice_progress_aggregated_analytics(client):
    """Verify /api/v1/practice/progress computes live metrics across all 4 skills."""
    res = await client.get("/api/v1/practice/progress")
    assert res.status_code == 200
    data = res.json()
    assert "reading" in data
    assert "listening" in data
    assert "writing" in data
    assert "speaking" in data
    assert "overall_skill_scores" in data
    assert "recent_activity" in data
    assert data["total_completed"] >= 0
