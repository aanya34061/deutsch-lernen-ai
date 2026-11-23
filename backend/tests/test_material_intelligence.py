from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.database import get_db
from app.services.material_intelligence_service import MaterialIntelligenceService, _sections, _source_sentence_questions
from test_library import SAMPLE_PDF_BYTES


def test_pdf_page_markers_are_preserved_as_sources():
    sections = _sections("--- Page 2 ---\nDer Hund ist hier.\n\n--- Page 4 ---\nDie Katze ist dort.")
    assert [(section["source_id"], section["source_ref"]) for section in sections] == [
        ("P2", "Page 2"), ("P4", "Page 4")
    ]


def test_source_fallback_masks_words_without_leaving_source_content():
    questions = _source_sentence_questions(
        [{"source_id": "P1", "source_ref": "Page 1", "text": "Ich wohne in Berlin. Das ist mein Buch."}],
        "material-id", "content-hash", "Unknown", "Introductions",
    )
    assert len(questions) == 2
    assert all(question["origin"] == "source_generated" for question in questions)
    assert all(question["correct_sentence_de"] in question["source_evidence"] for question in questions)
    assert all(question["correct_answer"] in question["source_evidence"] for question in questions)


@pytest.mark.asyncio
async def test_question_generation_discards_unverifiable_and_duplicate_items():
    sections = [{"source_id": "S1", "source_ref": "Section 1", "text": "Ich habe einen Apfel. Der Apfel ist rot."}]
    response = [
        {"type": "multiple_choice", "question": "Welches Obst habe ich?", "options": ["Apfel", "Birne", "Brot", "Wasser"], "correct_answer": "Apfel", "source_id": "S1", "evidence": "Ich habe einen Apfel.", "difficulty": "Easy"},
        {"type": "multiple_choice", "question": "Which fruit is mentioned?", "options": ["Apfel", "Birne", "Brot", "Wasser"], "correct_answer": "Apfel", "source_id": "S1", "evidence": "Not in this document.", "difficulty": "Easy"},
        {"type": "fill_blank", "question": "Ich _____ ein Auto.", "prompt": "Complete the sentence.", "correct_sentence_de": "Ich habe ein Auto.", "correct_answer": "habe", "source_id": "S1", "evidence": "Ich habe einen Apfel.", "difficulty": "Easy"},
        {"type": "multiple_choice", "question": "Welches Obst habe ich?", "options": ["Apfel", "Birne", "Brot", "Wasser"], "correct_answer": "Apfel", "source_id": "S1", "evidence": "Ich habe einen Apfel.", "difficulty": "Easy"},
    ]
    analysis = {"topic": "Food"}
    with patch.object(MaterialIntelligenceService, "_ask_json", new=AsyncMock(return_value=response)):
        result = await MaterialIntelligenceService._generate_questions("source", "A1", analysis, sections, "material-id", "hash")

    assert len(result) == 1
    assert result[0]["material_id"] == "material-id"
    assert result[0]["source_ref"] == "Section 1"
    assert result[0]["origin"] == "ai_generated"


@pytest.mark.asyncio
async def test_unsupported_note_examples_are_explicitly_labeled_generated():
    notes = {
        "introduction": "The source describes a learner.", "concepts": [], "grammar": [], "vocabulary": [
            {"word": "das Auto", "meaning_en": "car", "example_de": "Ich fahre Auto.", "source_id": "S1"}
        ], "examples": [{"german": "Ich fahre Auto.", "english": "I drive a car.", "source_id": "S1"}],
        "rules": [], "common_mistakes": [], "summary": "A learner is mentioned.",
    }
    with patch.object(MaterialIntelligenceService, "_ask_json", new=AsyncMock(return_value=notes)):
        result = await MaterialIntelligenceService._generate_notes(
            "[S1 | Section 1]\nIch lerne Deutsch.", "A1", {"topic": "Learning"}, {"S1"}
        )
    assert result["examples"][0]["generated"] is True
    assert result["vocabulary"] == []


@pytest.mark.asyncio
async def test_upload_generates_persistent_source_notes_questions_and_attempt(client: AsyncClient):
    analysis = {
        "cefr_level": "A1", "level_confidence": 0.9, "topic": "German study", "subtopics": [],
        "grammar_concepts": [], "vocabulary": [], "expressions": [], "learning_objectives": [],
        "important_rules": [], "existing_exercises": [],
    }
    notes = {
        "introduction": "The source says someone is learning German.", "concepts": [{"title": "Deutsch lernen", "explanation": "The text says Ich lerne gerade Deutsch.", "source_id": "P1"}],
        "grammar": [], "vocabulary": [], "examples": [], "rules": [], "common_mistakes": [], "summary": "Ich lerne gerade Deutsch.",
    }
    questions = [{
        "type": "multiple_choice", "question": "Was lernt die Person?", "options": ["Deutsch", "Englisch", "Französisch", "Spanisch"],
        "correct_answer": "Deutsch", "explanation_en": "The source says Deutsch.", "difficulty": "Easy", "skill": "vocabulary",
        "source_id": "P1", "evidence": "Ich lerne gerade Deutsch",
    }]
    with patch.object(MaterialIntelligenceService, "_ask_json", new=AsyncMock(side_effect=[analysis, notes, questions])):
        response = await client.post(
            "/api/v1/library/upload",
            files={"file": ("deutsch.pdf", SAMPLE_PDF_BYTES.replace(b"Hallo Welt German Lesson", b"Ich lerne gerade Deutsch"), "application/pdf")},
        )
    assert response.status_code == 201
    material_id = response.json()["id"]

    material = (await client.get(f"/api/v1/library/{material_id}")).json()
    assert material["processing_status"] == "ready"
    assert material["cefr_level"] == "A1"
    assert material["questions_count"] == 1
    assert "Ich lerne gerade Deutsch" in material["extracted_text"]

    note_response = await client.get(f"/api/v1/study/notes?material_id={material_id}")
    assert note_response.status_code == 200
    note = note_response.json()[0]
    assert "Page 1" in note["markdown"]
    assert note["content"]["concepts"][0]["title"] == "Deutsch lernen"

    edit_response = await client.put(f"/api/v1/study/notes/{note['id']}", json={"markdown": "My edited version."})
    assert edit_response.status_code == 200
    assert edit_response.json()["is_manually_edited"] is True
    next_version = {**notes, "introduction": "A new generated version.", "concepts": [{"title": "Deutsch lernen", "explanation": "The source says this.", "source_id": "P1"}]}
    with patch.object(MaterialIntelligenceService, "_ask_json", new=AsyncMock(return_value=next_version)):
        regenerate_response = await client.post(f"/api/v1/study/notes/{note['id']}/regenerate")
    assert regenerate_response.status_code == 200
    assert regenerate_response.json()["version"] == 2
    assert (await client.get(f"/api/v1/study/notes/{note['id']}")).json()["markdown"] == "My edited version."

    question_response = await client.get(f"/api/v1/study/questions?material_id={material_id}")
    question = question_response.json()[0]
    assert question["origin"] == "ai_generated"
    assert question["source_ref"] == "Page 1"
    assert "correct_answer" not in question

    wrong_attempt = await client.post(f"/api/v1/exercises/{question['id']}/submit", json={"user_answer": "Französisch"})
    assert wrong_attempt.status_code == 200
    incorrect = await client.get(f"/api/v1/study/questions?material_id={material_id}&incorrect_only=true")
    assert len(incorrect.json()) == 1
    attempt = await client.post(f"/api/v1/exercises/{question['id']}/submit", json={"user_answer": "Deutsch"})
    assert attempt.status_code == 200
    assert attempt.json()["is_correct"] is True
    assert (await client.get(f"/api/v1/study/questions?material_id={material_id}&incorrect_only=true")).json() == []

    # Same file bytes return the existing document and do not create another question set.
    with patch.object(MaterialIntelligenceService, "_ask_json", new=AsyncMock(side_effect=AssertionError("must not regenerate"))):
        duplicate = await client.post(
            "/api/v1/library/upload",
            files={"file": ("deutsch.pdf", SAMPLE_PDF_BYTES.replace(b"Hallo Welt German Lesson", b"Ich lerne gerade Deutsch"), "application/pdf")},
        )
    assert duplicate.json()["id"] == material_id
    assert (await client.get(f"/api/v1/study/questions?material_id={material_id}")).json().__len__() == 1


@pytest.mark.asyncio
async def test_empty_text_is_saved_as_failed_extraction(client: AsyncClient):
    response = await client.post("/api/v1/library/upload", files={"file": ("leer.txt", b"   ", "text/plain")})
    assert response.status_code == 201
    assert response.json()["status"] == "failed"
    assert response.json()["processing_status"] == "failed"
    assert response.json()["extracted_text"] == ""


@pytest.mark.asyncio
async def test_corrupt_pdf_is_preserved_and_reported_as_failed(client: AsyncClient):
    response = await client.post("/api/v1/library/upload", files={"file": ("broken.pdf", b"not a PDF", "application/pdf")})
    assert response.status_code == 201
    material = response.json()
    assert material["status"] == "failed"
    assert material["processing_status"] == "failed"
    assert material["extracted_text"] == ""
    downloaded = await client.get(f"/api/v1/library/{material['id']}/file")
    assert downloaded.status_code == 200
    assert downloaded.content == b"not a PDF"


@pytest.mark.asyncio
async def test_ai_failure_can_retry_without_duplicate_upload(client: AsyncClient):
    with patch.object(MaterialIntelligenceService, "_ask_json", new=AsyncMock(side_effect=RuntimeError("Ollama offline"))):
        response = await client.post("/api/v1/library/upload", files={"file": ("retry.txt", b"Ich lerne Deutsch.", "text/plain")})
    assert response.status_code == 201
    material_id = response.json()["id"]
    failed = (await client.get(f"/api/v1/library/{material_id}")).json()
    assert failed["processing_status"] == "failed"
    assert "Ollama offline" in failed["processing_error"]

    analysis = {"cefr_level": "Unknown", "level_confidence": 0.2, "topic": "General"}
    notes = {"introduction": "The source says the learner studies German.", "concepts": [{"title": "Learning", "explanation": "The learner studies German.", "source_id": "S1"}], "grammar": [], "vocabulary": [], "examples": [], "rules": [], "common_mistakes": [], "summary": "Ich lerne Deutsch."}
    questions = [{"type": "true_false", "question": "Ich lerne Deutsch.", "options": ["True", "False"], "correct_answer": "True", "explanation_en": "The sentence says this.", "difficulty": "Easy", "skill": "reading", "source_id": "S1", "evidence": "Ich lerne Deutsch."}]
    with patch.object(MaterialIntelligenceService, "_ask_json", new=AsyncMock(side_effect=[analysis, notes, questions])):
        retried = await client.post(f"/api/v1/library/{material_id}/process/retry")
    assert retried.status_code == 200
    ready = (await client.get(f"/api/v1/library/{material_id}")).json()
    assert ready["processing_status"] == "ready"
    assert ready["cefr_level"] == "Unknown"
    assert ready["questions_count"] == 1
    assert (await client.get(f"/api/v1/study/questions?material_id={material_id}")).json().__len__() == 1


@pytest.mark.asyncio
async def test_short_source_can_be_ready_with_notes_and_no_safe_questions(client: AsyncClient):
    analysis = {
        "cefr_level": "Unknown", "level_confidence": 0.1, "topic": "Greeting",
        "subtopics": [], "grammar_concepts": [], "vocabulary": [], "expressions": [],
        "learning_objectives": [], "important_rules": [], "existing_exercises": [],
    }
    notes = {
        "introduction": "The source contains a greeting.", "concepts": [], "grammar": [],
        "vocabulary": [], "examples": [], "rules": [], "common_mistakes": [], "summary": "Hallo.",
    }
    with patch.object(MaterialIntelligenceService, "_ask_json", new=AsyncMock(side_effect=[analysis, notes, []])), \
            patch("app.services.material_intelligence_service.RetrievalService.index_material", new=AsyncMock(return_value={"status": "indexed"})), \
            patch("app.services.material_intelligence_service.RetrievalService.update_material_metadata_in_chunks", new=AsyncMock()):
        response = await client.post(
            "/api/v1/library/upload",
            files={"file": ("greeting.txt", b"Hallo.", "text/plain")},
        )

    assert response.status_code == 201
    material = (await client.get(f"/api/v1/library/{response.json()['id']}")).json()
    assert material["processing_status"] == "ready"
    assert material["notes_count"] == 1
    assert material["questions_count"] == 0
    assert (await client.get(f"/api/v1/study/questions?material_id={material['id']}")).json() == []


@pytest.mark.asyncio
async def test_malformed_ai_questions_fall_back_to_persisted_source_practice(client: AsyncClient):
    analysis = {
        "cefr_level": "Unknown", "level_confidence": 0.1, "topic": "Introductions",
        "subtopics": [], "grammar_concepts": [], "vocabulary": [], "expressions": [],
        "learning_objectives": [], "important_rules": [], "existing_exercises": [],
    }
    notes = {
        "introduction": "The text says where the learner lives and who Max is.", "concepts": [],
        "grammar": [], "vocabulary": [], "examples": [], "rules": [], "common_mistakes": [],
        "summary": "Ich wohne in Berlin. Max ist mein Bruder.",
    }
    with patch.object(MaterialIntelligenceService, "_ask_json", new=AsyncMock(side_effect=[analysis, notes, [["malformed model output"]]])), \
            patch("app.services.material_intelligence_service.RetrievalService.index_material", new=AsyncMock(return_value={"status": "indexed"})), \
            patch("app.services.material_intelligence_service.RetrievalService.update_material_metadata_in_chunks", new=AsyncMock()):
        uploaded = await client.post(
            "/api/v1/library/upload",
            files={"file": ("introductions.txt", b"Ich wohne in Berlin. Max ist mein Bruder.", "text/plain")},
        )
    assert uploaded.status_code == 201
    material_id = uploaded.json()["id"]
    material = (await client.get(f"/api/v1/library/{material_id}")).json()
    questions = (await client.get(f"/api/v1/study/questions?material_id={material_id}")).json()
    assert material["processing_status"] == "ready"
    assert material["questions_count"] == 2
    assert len(questions) == 2
    assert all(item["origin"] == "source_generated" for item in questions)

    question = questions[0]
    answer = await get_db().exercises.find_one({"id": question["id"]})
    attempt = await client.post(f"/api/v1/exercises/{question['id']}/submit", json={"user_answer": answer["correct_answer"]})
    assert attempt.status_code == 200
    assert attempt.json()["is_correct"] is True
    assert await get_db().exercise_attempts.count_documents({"exercise_id": question["id"], "is_seeded": False}) == 1
