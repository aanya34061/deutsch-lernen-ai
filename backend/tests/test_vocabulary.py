import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_vocabulary_crud_and_status(client: AsyncClient):
    # 1. Create word manually
    new_word = {
        "word": "die Brille",
        "article": "die",
        "plural": "die Brillen",
        "meaning_en": "glasses / spectacles",
        "example_de": "Wo ist meine Brille?",
        "example_en": "Where are my glasses?",
        "cefr_level": "A1",
        "topic": "Accessories",
        "status": "new"
    }
    res_create = await client.post("/api/v1/vocabulary", json=new_word)
    assert res_create.status_code == 201
    created = res_create.json()
    vocab_id = created["id"]
    assert created["word"] == "die Brille"
    assert created["status"] == "new"

    # 2. List vocabulary and search
    res_list = await client.get("/api/v1/vocabulary?search=Brille")
    assert res_list.status_code == 200
    found = res_list.json()
    assert len(found) >= 1
    assert any(item["word"] == "die Brille" for item in found)

    # 3. Update status to mastered
    res_update = await client.patch(f"/api/v1/vocabulary/{vocab_id}", json={"status": "mastered"})
    assert res_update.status_code == 200
    updated = res_update.json()
    assert updated["status"] == "mastered"
    assert updated["mastery_score"] == 100

    # 4. Delete vocabulary
    res_del = await client.delete(f"/api/v1/vocabulary/{vocab_id}")
    assert res_del.status_code == 200

@pytest.mark.asyncio
async def test_vocabulary_batch_creation(client: AsyncClient):
    batch_data = {
        "source_type": "lesson",
        "source_id": "a1-lesson-1",
        "source_title": "Greetings",
        "words": [
            {
                "word": "der Abend",
                "article": "der",
                "meaning_en": "the evening",
                "cefr_level": "A1",
                "topic": "Time"
            },
            {
                "word": "der Morgen",
                "article": "der",
                "meaning_en": "the morning",
                "cefr_level": "A1",
                "topic": "Time"
            }
        ]
    }
    res = await client.post("/api/v1/vocabulary/batch", json=batch_data)
    assert res.status_code == 201
    assert res.json()["saved_count"] >= 1

@pytest.mark.asyncio
async def test_extract_vocabulary_from_text(client: AsyncClient):
    sample_text = "Ich trinke gern Kaffee und Wasser. Morgens esse ich Brot und einen Apfel."
    res = await client.post("/api/v1/vocabulary/extract-from-material", json={"text": sample_text})
    assert res.status_code == 200
    data = res.json()
    assert data["total_found"] > 0
    words = [item["word"].lower() for item in data["items"]]
    assert any("kaffee" in w for w in words)
    assert any("brot" in w for w in words)
    assert any("apfel" in w for w in words)
