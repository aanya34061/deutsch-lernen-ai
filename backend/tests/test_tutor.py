import pytest
from unittest.mock import patch, AsyncMock
from bson import ObjectId

from app.config import settings
from app.database import get_db
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.retrieval_service import RetrievalService
from app.services.ollama_service import (
    OllamaService,
    OllamaNotRunningError,
    OllamaModelMissingError
)
from app.services.ai_exercise_service import AiExerciseService
from app.services.tutor_service import TutorService
from app.security import _current_user_id


def test_location_question_is_answered_from_exact_retrieved_sentence():
    answer = TutorService._source_location_answer(
        "According to my notes, where does Anna live?",
        [{
            "text": "--- Page 1 ---\nIch bin Anna.\nWir wohnen in Berlin. (We live in Berlin.)",
            "source_title": "A1 Introductions", "page_number": 1,
        }],
    )
    assert answer is not None
    assert "Wir wohnen in Berlin" in answer
    assert "inference" in answer
    assert "A1 Introductions, page 1" in answer

@pytest.mark.asyncio
async def test_text_chunking_and_metadata_preservation():
    """Verify that ChunkingService splits text, handles overlap, and preserves page numbers."""
    paged_text = (
        "--- Page 1 ---\n"
        "Der Apfel ist eine Frucht. Er schmeckt süß und frisch. Die Banane ist gelb.\n\n"
        "--- Page 2 ---\n"
        "Das Auto fährt auf der Straße. Der Zug fährt auf den Schienen.\n"
        "Wir reisen gerne nach Berlin."
    )
    chunks = ChunkingService.chunk_material(
        material_id="mat_123",
        text=paged_text,
        title="Test Grammar Note",
        original_filename="grammar.pdf",
        cefr_level="A1",
        topic="Vocabulary",
        chunk_size=120,
        chunk_overlap=20
    )

    assert len(chunks) >= 2
    # Check first chunk metadata
    assert chunks[0]["material_id"] == "mat_123"
    assert chunks[0]["page_number"] == 1
    assert chunks[0]["cefr_level"] == "A1"
    assert chunks[0]["topic"] == "Vocabulary"
    assert "Apfel" in chunks[0]["text"]
    assert chunks[0]["content_hash"] != ""

    # Check that page 2 chunk has page_number 2
    page2_chunks = [c for c in chunks if c["page_number"] == 2]
    assert len(page2_chunks) > 0
    assert "Auto" in page2_chunks[0]["text"]

@pytest.mark.asyncio
async def test_embedding_and_cosine_similarity():
    """Verify deterministic local vector embeddings and cosine similarity properties."""
    v1 = await EmbeddingService.embed_text("der Apfel und das Buch")
    v2 = await EmbeddingService.embed_text("der Apfel und das Buch")
    v3 = await EmbeddingService.embed_text("der Zug fährt schnell nach München")

    # Identical texts must have similarity == 1.0
    sim_identical = EmbeddingService.cosine_similarity(v1, v2)
    assert pytest.approx(sim_identical, 0.001) == 1.0

    # Dissimilar texts should have much lower similarity
    sim_different = EmbeddingService.cosine_similarity(v1, v3)
    assert sim_different < sim_identical

@pytest.mark.asyncio
async def test_content_hash_prevents_duplicate_embedding():
    """Verify that materials with unchanged content are not re-embedded."""
    db = get_db()
    mat_doc = {
        "title": "Unchanged Notes",
        "user_id": "default",
        "file_type": "txt",
        "source_type": "upload",
        "cefr_level": "A1",
        "topic": "Grammar",
        "status": "ready",
        "extracted_text": "Die Katze schläft auf dem Sofa. Der Hund spielt im Garten."
    }
    insert_res = await db.materials.insert_one(mat_doc)
    mat_id = str(insert_res.inserted_id)

    # First indexing
    res1 = await RetrievalService.index_material(mat_id)
    assert res1["status"] == "indexed"
    assert res1.get("skipped") is not True

    # Second indexing without force should skip
    res2 = await RetrievalService.index_material(mat_id, force=False)
    assert res2["status"] == "indexed"
    assert res2.get("skipped") is True

    # Cleanup
    await db.materials.delete_one({"_id": insert_res.inserted_id})
    await RetrievalService.delete_material_chunks(mat_id)

@pytest.mark.asyncio
async def test_retrieval_relevance_and_selected_source_filtering():
    """Verify retrieval returns relevant chunks and strictly respects material_id filter."""
    db = get_db()
    # Create two materials
    m1 = await db.materials.insert_one({
        "title": "Articles Guide",
        "user_id": "default",
        "cefr_level": "A1",
        "topic": "Articles",
        "extracted_text": "Der Apfel ist maskulin. Die Birne ist feminin. Das Buch ist neutral."
    })
    m1_id = str(m1.inserted_id)
    await RetrievalService.index_material(m1_id)

    m2 = await db.materials.insert_one({
        "title": "Separable Verbs",
        "user_id": "default",
        "cefr_level": "A2",
        "topic": "Verbs",
        "extracted_text": "Aufstehen ist ein trennbares Verb. Ich stehe um 7 Uhr auf."
    })
    m2_id = str(m2.inserted_id)
    await RetrievalService.index_material(m2_id)

    # 1. Search for articles without filter
    res_general = await RetrievalService.retrieve_relevant_chunks(
        query="Welcher Artikel hat Apfel?",
        cefr_level="A1"
    )
    assert len(res_general) > 0
    assert any("Apfel" in c["text"] for c in res_general)

    # 2. Search restricted to m2 (Separable Verbs)
    res_filtered = await RetrievalService.retrieve_relevant_chunks(
        query="Welcher Artikel hat Apfel?",
        material_id=m2_id
    )
    # None of the results should be from m1!
    for c in res_filtered:
        assert c["material_id"] == m2_id

    # Cleanup
    await db.materials.delete_one({"_id": m1.inserted_id})
    await db.materials.delete_one({"_id": m2.inserted_id})
    await RetrievalService.delete_material_chunks(m1_id)
    await RetrievalService.delete_material_chunks(m2_id)

@pytest.mark.asyncio
async def test_deleted_material_cleans_up_chunks(client):
    """Verify that deleting a material removes all its indexed knowledge chunks."""
    db = get_db()
    owner_token = _current_user_id.set(client.user_id)
    try:
        mat = await db.materials.insert_one({
        "title": "Temporary Study Note",
        "user_id": client.user_id,
        "file_type": "txt",
        "source_type": "upload",
        "cefr_level": "A1",
        "topic": "General",
        "status": "ready",
        "extracted_text": "Guten Morgen! Wie geht es Ihnen? Danke, gut."
        })
        mat_id = str(mat.inserted_id)
        await RetrievalService.index_material(mat_id)
    finally:
        _current_user_id.reset(owner_token)

    # Check chunks exist
    chunk_count_before = await db.knowledge_chunks.count_documents({"material_id": mat_id})
    assert chunk_count_before > 0

    # Delete material via API
    del_res = await client.delete(f"/api/v1/library/{mat_id}")
    assert del_res.status_code == 200

    # Verify chunks were wiped
    chunk_count_after = await db.knowledge_chunks.count_documents({"material_id": mat_id})
    assert chunk_count_after == 0

@pytest.mark.asyncio
async def test_tutor_status_endpoint(client):
    """Verify /api/v1/tutor/status reports connection status without failing when Ollama is offline."""
    res = await client.get("/api/v1/tutor/status")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert data["status"] in ["ready", "model_not_installed", "ollama_not_running", "error", "disabled", "not_configured"]
    assert "configured_model" in data or data["status"] == "disabled"
    assert "indexing" in data
    assert "total_chunks" in data["indexing"]

@pytest.mark.asyncio
async def test_tutor_chat_when_ollama_unavailable(client, monkeypatch):
    """Verify clear 503 error with setup message when Ollama is not running."""
    monkeypatch.setattr(settings, "AI_PROVIDER", "ollama")
    monkeypatch.setattr(settings, "OLLAMA_BASE_URL", "http://test-ollama")
    with patch.object(
        OllamaService,
        "check_status",
        new=AsyncMock(return_value={
            "status": "ollama_not_running",
            "is_ready": False,
            "is_running": False,
            "setup_instructions": "Start Ollama via 'ollama serve'"
        })
    ):
        res = await client.post("/api/v1/tutor/chat", json={
            "message": "Explain the difference between nicht and kein.",
            "cefr_level": "A1"
        })
        assert res.status_code == 503
        data = res.json()
        assert "Ollama is not running" in data["detail"]

@pytest.mark.asyncio
async def test_tutor_chat_when_model_missing(client, monkeypatch):
    """Verify clear 503 error with pull instructions when model is not installed."""
    monkeypatch.setattr(settings, "AI_PROVIDER", "ollama")
    monkeypatch.setattr(settings, "OLLAMA_BASE_URL", "http://test-ollama")
    with patch.object(
        OllamaService,
        "check_status",
        new=AsyncMock(return_value={
            "status": "model_not_installed",
            "is_ready": False,
            "is_running": True,
            "model_available": False,
            "setup_instructions": f"Run 'ollama pull {settings.OLLAMA_MODEL}'"
        })
    ):
        res = await client.post("/api/v1/tutor/chat", json={
            "message": "Explain der, die, das.",
            "cefr_level": "A1"
        })
        assert res.status_code == 503
        assert f"ollama pull {settings.OLLAMA_MODEL}" in res.json()["detail"]

@pytest.mark.asyncio
async def test_tutor_chat_success_and_source_attribution(client):
    """Verify mocked successful chat with RAG source attribution and conversation persistence."""
    db = get_db()
    # Add indexed material
    owner_token = _current_user_id.set(client.user_id)
    try:
        mat = await db.materials.insert_one({
        "title": "A1 Negation Guide",
        "user_id": client.user_id,
        "cefr_level": "A1",
        "topic": "Negation",
        "extracted_text": "Nicht verneint Verben und Adjektive. Kein verneint Nomen mit unbestimmtem Artikel."
        })
        mat_id = str(mat.inserted_id)
        await RetrievalService.index_material(mat_id)
    finally:
        _current_user_id.reset(owner_token)

    mock_reply = (
        "Here is the simple rule for A1 learners:\n\n"
        "1. **Kein**: used to negate nouns that take 'ein' or no article (e.g., 'Ich habe kein Buch').\n"
        "2. **Nicht**: used to negate verbs, adjectives, or specific nouns with 'der/die/das'.\n\n"
        "According to your uploaded 'A1 Negation Guide': Nicht verneint Verben, kein verneint Nomen."
    )

    with patch.object(
        OllamaService,
        "check_status",
        new=AsyncMock(return_value={
            "status": "ready",
            "is_ready": True,
            "is_running": True,
            "model_available": True
        })
    ), patch.object(
        OllamaService,
        "generate_chat",
        new=AsyncMock(return_value=mock_reply)
    ):
        chat_res = await client.post("/api/v1/tutor/chat", json={
            "message": "Explain the difference between nicht and kein.",
            "cefr_level": "A1",
            "material_id": mat_id
        })
        assert chat_res.status_code == 200
        data = chat_res.json()
        assert data["role"] == "assistant"
        assert "Kein" in data["message"]
        assert data["is_rag"] is True
        assert len(data["sources"]) > 0
        assert data["sources"][0]["material_id"] == mat_id
        assert "conversation_id" in data

        conv_id = data["conversation_id"]

        # Follow-up in the same conversation
        follow_up_res = await client.post("/api/v1/tutor/chat", json={
            "message": "Can you give me an example with 'kein'?",
            "conversation_id": conv_id,
            "cefr_level": "A1"
        })
        assert follow_up_res.status_code == 200
        assert follow_up_res.json()["conversation_id"] == conv_id

        # Verify conversation retrieval endpoint
        get_conv = await client.get(f"/api/v1/tutor/conversations/{conv_id}")
        assert get_conv.status_code == 200
        conv_data = get_conv.json()
        # 2 questions + 2 assistant answers = 4 messages
        assert len(conv_data["messages"]) == 4

        # Delete conversation
        del_conv = await client.delete(f"/api/v1/tutor/conversations/{conv_id}")
        assert del_conv.status_code == 200

    # Cleanup
    await db.materials.delete_one({"_id": mat.inserted_id})
    await RetrievalService.delete_material_chunks(mat_id)

@pytest.mark.asyncio
async def test_chat_payload_validation(client):
    """Verify input validation: empty message and oversized message rejected."""
    # Empty message
    res_empty = await client.post("/api/v1/tutor/chat", json={"message": "   "})
    assert res_empty.status_code in [400, 422]

    # Oversized message
    huge_msg = "A" * 2500
    res_huge = await client.post("/api/v1/tutor/chat", json={"message": huge_msg})
    assert res_huge.status_code == 422

@pytest.mark.asyncio
async def test_ai_exercise_generation_and_malformed_handling(client):
    """Malformed AI output may use authored fallback questions, never AI labels."""
    with patch.object(
        OllamaService,
        "check_status",
        new=AsyncMock(return_value={"status": "ready", "is_ready": True})
    ), patch.object(
        OllamaService,
        "generate_chat",
        new=AsyncMock(return_value="I am an AI and here are some thoughts without valid JSON at all!")
    ):
        gen_res = await client.post("/api/v1/tutor/exercises/generate", json={
            "cefr_level": "A1",
            "count": 3
        })
        assert gen_res.status_code == 200
        generated_ids = [item["id"] for item in gen_res.json()]
        assert len(generated_ids) == 3
        fallback_docs = await get_db().exercises.find({"id": {"$in": generated_ids}}).to_list(length=3)
        assert len(fallback_docs) == 3
        assert all(item["is_ai_generated"] is False for item in fallback_docs)
        await get_db().exercises.delete_many({"id": {"$in": generated_ids}})

@pytest.mark.asyncio
async def test_index_rebuild_and_retry_endpoints(client):
    """Verify /api/v1/tutor/index/rebuild and /api/v1/tutor/index/retry/{id}."""
    db = get_db()
    mat = await db.materials.insert_one({
        "title": "Index Test Document",
        "user_id": client.user_id,
        "file_type": "txt",
        "source_type": "upload",
        "cefr_level": "A1",
        "topic": "General",
        "extracted_text": "Das ist ein einfacher Testtext für das Indexing."
    })
    mat_id = str(mat.inserted_id)

    # Retry single material index
    retry_res = await client.post(f"/api/v1/tutor/index/retry/{mat_id}")
    assert retry_res.status_code == 200
    assert retry_res.json()["status"] == "indexed"

    # Rebuild all indexes
    rebuild_res = await client.post("/api/v1/tutor/index/rebuild")
    assert rebuild_res.status_code == 200
    assert rebuild_res.json()["total_processed"] >= 1

    # Index status check
    status_res = await client.get("/api/v1/tutor/index/status")
    assert status_res.status_code == 200
    assert status_res.json()["total_chunks"] >= 1

    # Cleanup
    await db.materials.delete_one({"_id": mat.inserted_id})
    await RetrievalService.delete_material_chunks(mat_id)
