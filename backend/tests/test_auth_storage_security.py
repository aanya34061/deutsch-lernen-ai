from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.database import get_db
from app.main import app
from app.services.storage_service import ObjectStorage


@pytest.mark.asyncio
async def test_api_requires_session_and_login_logout(client):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as anonymous:
        response = await anonymous.get("/api/v1/dashboard")
        assert response.status_code == 401

    account = await get_db().accounts.find_one({"username": client.username})
    assert account["password_hash"] != client.password
    assert "password" not in account
    assert account["password_iterations"] >= 310_000

    await client.post("/api/v1/auth/logout")
    assert (await client.get("/api/v1/dashboard")).status_code == 401

    logged_in = await client.post("/api/v1/auth/login", json={
        "username": client.username,
        "password": client.password,
    })
    assert logged_in.status_code == 200
    client.headers["X-CSRF-Token"] = logged_in.json()["csrf_token"]
    assert (await client.get("/api/v1/dashboard")).status_code == 200


@pytest.mark.asyncio
async def test_same_origin_api_requests_are_allowed_without_cors_allowlist(client):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Origin": "http://test"},
    ) as same_origin:
        assert (await same_origin.get("/api/v1/dashboard")).status_code == 401

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Origin": "https://attacker.invalid"},
    ) as cross_origin:
        assert (await cross_origin.get("/api/v1/dashboard")).status_code == 403


@pytest.mark.asyncio
async def test_learner_records_and_material_files_are_owner_scoped(client):
    created = await client.post(
        "/api/v1/library/upload",
        files={"file": ("owned.txt", b"Ich lerne Deutsch.", "text/plain")},
    )
    assert created.status_code == 201
    material_id = created.json()["id"]

    own_word = await client.post("/api/v1/vocabulary", json={
        "word": "das Testwort", "meaning_en": "test word", "cefr_level": "A1",
    })
    assert own_word.status_code == 201
    vocab_id = own_word.json()["id"]

    note = await get_db().study_notes.insert_one({
        "user_id": client.user_id,
        "material_id": material_id,
        "is_current": True,
        "markdown": "private note",
        "content": {"introduction": "private"},
    })
    question_id = "private-question"
    await get_db().exercises.insert_one({
        "id": question_id,
        "user_id": client.user_id,
        "is_seeded": False,
        "origin": "ai_generated",
        "question": "Private question",
        "type": "true_false",
        "correct_answer": True,
    })

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as other:
        credentials = {"username": "other-learner", "password": "Different-Passphrase-7582!"}
        registered = await other.post("/api/v1/auth/register", json=credentials)
        assert registered.status_code == 201
        other.headers["X-CSRF-Token"] = registered.json()["csrf_token"]

        assert (await other.get(f"/api/v1/library/{material_id}")).status_code == 404
        assert (await other.get(f"/api/v1/library/{material_id}/file")).status_code == 404
        assert (await other.patch(f"/api/v1/library/{material_id}", json={"title": "stolen"})).status_code == 404
        assert (await other.delete(f"/api/v1/library/{material_id}")).status_code == 404
        other_vocabulary = (await other.get("/api/v1/vocabulary")).json()
        assert all(item["id"] != vocab_id for item in other_vocabulary)
        assert (await other.patch(f"/api/v1/vocabulary/{vocab_id}", json={"status": "mastered"})).status_code == 404
        assert (await other.get(f"/api/v1/study/notes/{note.inserted_id}")).status_code == 404
        assert (await other.get(f"/api/v1/exercises/{question_id}")).status_code == 404
        assert (await other.get("/api/v1/study/questions")).json() == []

    assert (await client.get(f"/api/v1/library/{material_id}")).status_code == 200
    assert (await client.get(f"/api/v1/library/{material_id}/file")).status_code == 200
    assert (await client.get(f"/api/v1/study/notes/{note.inserted_id}")).status_code == 200
    own_vocabulary = (await client.get("/api/v1/vocabulary")).json()
    assert any(item["id"] == vocab_id for item in own_vocabulary)


@pytest.mark.asyncio
async def test_private_object_storage_survives_local_file_removal(monkeypatch, tmp_path):
    objects = {}

    class MemoryS3:
        def upload_file(self, filename, bucket, key, ExtraArgs=None):
            objects[(bucket, key)] = Path(filename).read_bytes()

        def download_file(self, bucket, key, filename):
            Path(filename).write_bytes(objects[(bucket, key)])

        def generate_presigned_url(self, operation, Params, ExpiresIn):
            return f"https://private-storage.invalid/{Params['Key']}?expires={ExpiresIn}"

        def delete_object(self, Bucket, Key):
            objects.pop((Bucket, Key), None)

    monkeypatch.setattr(ObjectStorage, "_client", staticmethod(lambda: MemoryS3()))
    monkeypatch.setattr(settings, "S3_BUCKET", "private-test-bucket")
    monkeypatch.setattr(settings, "S3_ACCESS_KEY_ID", "test-key")
    monkeypatch.setattr(settings, "S3_SECRET_ACCESS_KEY", "test-secret")

    source = tmp_path / "source.txt"
    source.write_bytes(b"durable German study file")
    await ObjectStorage.upload_file(source, "learner/material/source.txt", "source.txt")
    source.unlink()

    restored = await ObjectStorage.download_to_temp("learner/material/source.txt")
    try:
        assert restored.read_bytes() == b"durable German study file"
        signed_url = await ObjectStorage.presigned_download_url("learner/material/source.txt", "source.txt")
        assert "expires=" in signed_url
    finally:
        restored.unlink(missing_ok=True)

    await ObjectStorage.delete_file("learner/material/source.txt")
    assert not objects
