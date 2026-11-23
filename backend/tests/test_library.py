import io
from types import SimpleNamespace
from unittest.mock import AsyncMock
import httpx
import pytest
from httpx import AsyncClient
from starlette.datastructures import UploadFile as StarletteUploadFile
import docx
from PIL import Image
from pathlib import Path
from app.config import settings
from app.services.library_service import (
    LibraryService,
    is_within_upload_dir,
)
from app.services.extractor_service import ExtractorService, _PinnedURLTransport
from app.models.material import LearningLinkCreate


def test_upload_path_containment_rejects_sibling_prefix(tmp_path):
    upload_dir = tmp_path / "uploads"
    sibling = tmp_path / "uploads-outside" / "private.txt"
    assert is_within_upload_dir(upload_dir / "safe.txt", upload_dir)
    assert not is_within_upload_dir(sibling, upload_dir)


@pytest.mark.asyncio
async def test_upload_file_is_removed_when_metadata_persistence_fails(monkeypatch, tmp_path):
    class FailedMaterials:
        async def find_one(self, _query):
            return None

        async def insert_one(self, document):
            assert document["is_seeded"] is False
            raise RuntimeError("database unavailable")

    class FailedDatabase:
        materials = FailedMaterials()

    monkeypatch.setattr("app.services.library_service.get_db", lambda: FailedDatabase())
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setattr(
        "app.services.library_service.ExtractorService.extract_file_content",
        lambda *_args: {"text": "Guten Tag", "summary": "Test"},
    )
    upload = StarletteUploadFile(filename="lesson.txt", file=io.BytesIO(b"Guten Tag"))

    with pytest.raises(RuntimeError):
        await LibraryService.upload_file(upload)

    assert list((tmp_path / "uploads").iterdir()) == []


@pytest.mark.asyncio
async def test_library_list_only_returns_unseeded_records_owned_by_default_user(monkeypatch):
    class Cursor:
        def __init__(self, docs):
            self.docs = docs

        def sort(self, *_args):
            return self

        def skip(self, _skip):
            return self

        def limit(self, _limit):
            return self

        async def to_list(self, length):
            return self.docs[:length]

    class Materials:
        def __init__(self):
            self.docs = [
                {"_id": "seeded", "title": "Seeded", "user_id": "default", "is_seeded": True},
                {"_id": "other", "title": "Other user's notes", "user_id": "other", "is_seeded": False},
                {"_id": "real", "title": "My uploaded notes", "user_id": "default", "is_seeded": False},
            ]
            self.query = None

        def matching(self, query):
            return [doc for doc in self.docs if doc.get("user_id") == query["user_id"] and doc.get("is_seeded") is not True]

        async def count_documents(self, query):
            self.query = query
            return len(self.matching(query))

        def find(self, query):
            return Cursor(self.matching(query))

    materials = Materials()
    class Database:
        pass
    db = Database()
    db.materials = materials
    monkeypatch.setattr("app.services.library_service.get_db", lambda: db)

    result = await LibraryService.list_materials()

    assert result.total == 1
    assert [item.title for item in result.items] == ["My uploaded notes"]
    assert materials.query["is_seeded"] == {"$ne": True}
    assert materials.query["user_id"] == "default"


@pytest.mark.asyncio
async def test_added_learning_link_is_marked_as_user_content(monkeypatch):
    class Materials:
        inserted = None

        async def find_one(self, _query):
            return None

        async def insert_one(self, document):
            self.inserted = document
            return SimpleNamespace(inserted_id="library-record-id")

    materials = Materials()
    class Database:
        pass
    db = Database()
    db.materials = materials
    monkeypatch.setattr("app.services.library_service.get_db", lambda: db)
    monkeypatch.setattr("app.services.library_service.ExtractorService.parse_youtube_video_id", lambda _url: None)
    monkeypatch.setattr("app.services.library_service.ExtractorService.is_public_http_url", lambda _url: _async_true())
    async def extract(_url):
        return {"title": "A German article", "text": "", "summary": "Article", "error": None}
    monkeypatch.setattr("app.services.library_service.ExtractorService.extract_from_web_url", extract)

    await LibraryService.add_learning_link(LearningLinkCreate(url="https://example.org/german"))

    assert materials.inserted["source_type"] == "link"
    assert materials.inserted["is_seeded"] is False


async def _async_true():
    return True

SAMPLE_PDF_BYTES = b"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >> endobj
4 0 obj << /Length 55 >> stream
BT
/F1 12 Tf
72 712 Td
(Hallo Welt German Lesson) Tj
ET
endstream
endobj
5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000222 00000 n 
0000000327 00000 n 
trailer << /Size 6 /Root 1 0 R >>
startxref
406
%%EOF"""

def create_sample_docx(text: str = "Deutsche Grammatik: Die vier Fälle") -> bytes:
    doc = docx.Document()
    doc.add_heading("German Grammar Lesson", level=1)
    doc.add_paragraph(text)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()

def create_sample_image() -> bytes:
    img = Image.new("RGB", (120, 60), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.mark.asyncio
async def test_upload_txt_file(client: AsyncClient):
    txt_content = "Lektion 1: Begrüßungen\nHallo! Wie geht es dir?\nMir geht es gut, danke!"
    files = {"file": ("lektion1.txt", txt_content.encode("utf-8"), "text/plain")}
    data = {
        "title": "A1 Begrüßungen Lektion",
        "cefr_level": "A1",
        "topic": "Grammar",
        "description": "Essential German greetings for beginner class"
    }

    res = await client.post("/api/v1/library/upload", files=files, data=data)
    assert res.status_code == 201
    payload = res.json()
    assert payload["title"] == "A1 Begrüßungen Lektion"
    assert payload["file_type"] == "txt"
    assert payload["cefr_level"] == "A1"
    assert payload["topic"] == "Grammar"
    assert payload["status"] == "ready"
    assert "Hallo! Wie geht es dir?" in payload["extracted_text"]
    assert payload["storage_filename"] is not None


@pytest.mark.asyncio
async def test_duplicate_upload_reuses_existing_material(client: AsyncClient):
    files = {"file": ("same-note.txt", b"Einmal speichern", "text/plain")}
    first = await client.post("/api/v1/library/upload", files=files)
    second = await client.post("/api/v1/library/upload", files=files)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert second.json()["user_id"] == client.user_id


@pytest.mark.asyncio
async def test_upload_pdf_file(client: AsyncClient):
    files = {"file": ("deutsch_lesson.pdf", SAMPLE_PDF_BYTES, "application/pdf")}
    data = {
        "title": "PDF German Lesson",
        "cefr_level": "A2",
        "topic": "Lesen"
    }

    res = await client.post("/api/v1/library/upload", files=files, data=data)
    assert res.status_code == 201
    payload = res.json()
    assert payload["file_type"] == "pdf"
    assert payload["cefr_level"] == "A2"
    assert payload["topic"] == "Lesen"
    assert "Hallo Welt German Lesson" in payload["extracted_text"]


@pytest.mark.asyncio
async def test_upload_docx_file(client: AsyncClient):
    docx_bytes = create_sample_docx("Präpositionen mit Dativ und Akkusativ")
    files = {"file": ("cases.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    data = {
        "title": "German Cases Guide",
        "cefr_level": "B1",
        "topic": "Grammar"
    }

    res = await client.post("/api/v1/library/upload", files=files, data=data)
    assert res.status_code == 201
    payload = res.json()
    assert payload["file_type"] == "docx"
    assert payload["cefr_level"] == "B1"
    assert "Präpositionen mit Dativ und Akkusativ" in payload["extracted_text"]


@pytest.mark.asyncio
async def test_upload_image_file(client: AsyncClient):
    img_bytes = create_sample_image()
    files = {"file": ("handwritten_notes.png", img_bytes, "image/png")}
    data = {
        "title": "Handwritten Notes Image",
        "cefr_level": "A1",
        "topic": "Schreiben"
    }

    res = await client.post("/api/v1/library/upload", files=files, data=data)
    assert res.status_code == 201
    payload = res.json()
    assert payload["file_type"] == "image"
    assert payload["status"] == "failed"
    assert payload["extracted_text"] == ""
    assert "OCR" in payload["error_message"]


@pytest.mark.asyncio
async def test_upload_unsupported_file_type(client: AsyncClient):
    files = {"file": ("malicious.exe", b"binarycontent", "application/octet-stream")}
    res = await client.post("/api/v1/library/upload", files=files, data={"cefr_level": "A1"})
    assert res.status_code == 400
    assert "Unsupported file type" in res.json()["detail"]


@pytest.mark.asyncio
async def test_path_traversal_sanitization(client: AsyncClient):
    # Attempt filename traversal attack
    files = {"file": ("../../evil_hack.txt", b"Safe content", "text/plain")}
    res = await client.post("/api/v1/library/upload", files=files, data={"cefr_level": "A1"})
    assert res.status_code == 201
    payload = res.json()
    assert ".." not in payload["original_filename"]
    assert ".." not in payload["storage_filename"]


@pytest.mark.asyncio
async def test_add_youtube_link(client: AsyncClient):
    data = {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "title": "German Pronunciation Video",
        "cefr_level": "A1",
        "topic": "Hören",
        "description": "Short YouTube practice video"
    }
    res = await client.post("/api/v1/library/links", json=data)
    assert res.status_code == 201
    payload = res.json()
    assert payload["file_type"] == "youtube"
    assert payload["source_type"] == "link"
    assert payload["source_url"] == data["url"]
    assert payload["status"] in {"ready", "failed"}
    if payload["status"] == "failed":
        assert "transcript" in payload["error_message"].lower()
        assert payload["extracted_text"] == ""


@pytest.mark.asyncio
async def test_add_general_web_link(client: AsyncClient):
    data = {
        "url": "https://example.com",
        "title": "Example German Practice Portal",
        "cefr_level": "A2",
        "topic": "Lesen"
    }
    res = await client.post("/api/v1/library/links", json=data)
    assert res.status_code == 201
    payload = res.json()
    assert payload["file_type"] == "link"
    assert payload["source_type"] == "link"
    assert payload["status"] in {"ready", "failed"}
    if payload["status"] == "failed":
        assert payload["error_message"]


@pytest.mark.asyncio
async def test_add_invalid_url(client: AsyncClient):
    data = {"url": "not-a-valid-url", "cefr_level": "A1"}
    res = await client.post("/api/v1/library/links", json=data)
    assert res.status_code == 400
    assert "URL must start with" in res.json()["detail"]


@pytest.mark.asyncio
async def test_add_link_rejects_local_or_private_destinations(client: AsyncClient):
    for url in ("http://127.0.0.1/private", "http://localhost/admin", "http://169.254.169.254/latest/meta-data/"):
        response = await client.post("/api/v1/library/links", json={"url": url, "cefr_level": "A1"})
        assert response.status_code == 400
        assert "public HTTP(S)" in response.json()["detail"]


@pytest.mark.asyncio
async def test_web_fetch_revalidates_redirect_destinations(monkeypatch):
    requests = []

    def redirect_to_local(request):
        requests.append((
            request.url.host,
            request.headers.get("host"),
            request.extensions.get("sni_hostname"),
        ))
        return httpx.Response(302, headers={"Location": "http://127.0.0.1/private"})

    upstream = httpx.MockTransport(redirect_to_local)
    monkeypatch.setattr(
        ExtractorService, "resolve_public_http_address", AsyncMock(side_effect=["93.184.216.34", None])
    )
    monkeypatch.setattr(
        "app.services.extractor_service._PinnedURLTransport",
        lambda address, hostname: _PinnedURLTransport(address, hostname, upstream=upstream),
    )
    result = await ExtractorService.extract_from_web_url("https://learn.example/article")
    assert result["has_text"] is False
    assert "publicly accessible" in result["error"]
    assert requests == [("93.184.216.34", "learn.example", b"learn.example")]


@pytest.mark.asyncio
async def test_url_resolver_rejects_a_hostname_with_any_non_public_dns_answer(monkeypatch):
    import socket

    records = [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0)),
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 0)),
    ]
    monkeypatch.setattr(socket, "getaddrinfo", lambda *_args, **_kwargs: records)

    address = await ExtractorService.resolve_public_http_address("https://rebinding.example/article")

    assert address is None


def test_pinned_url_transport_disables_environment_proxy_resolution(monkeypatch):
    options = {}

    class Transport:
        def __init__(self, **kwargs):
            options.update(kwargs)

    monkeypatch.setattr("app.services.extractor_service.httpx.AsyncHTTPTransport", Transport)
    _PinnedURLTransport("93.184.216.34", "example.org")

    assert options == {"trust_env": False}


@pytest.mark.asyncio
async def test_list_materials_and_filtering(client: AsyncClient):
    # Seed a specific item
    txt = "Spezifischer Text zum Suchen und Finden."
    files = {"file": ("search_test.txt", txt.encode("utf-8"), "text/plain")}
    await client.post(
        "/api/v1/library/upload",
        files=files,
        data={"title": "UniqueSearchTitle123", "cefr_level": "B2", "topic": "Sprechen"}
    )

    # 1. List all
    res = await client.get("/api/v1/library")
    assert res.status_code == 200
    list_payload = res.json()
    assert "items" in list_payload
    assert list_payload["total"] > 0

    # 2. Filter by level
    res_b2 = await client.get("/api/v1/library?level=B2")
    assert res_b2.status_code == 200
    assert all(item["cefr_level"] == "B2" for item in res_b2.json()["items"])

    # 3. Filter by file_type
    res_txt = await client.get("/api/v1/library?file_type=txt")
    assert res_txt.status_code == 200
    assert all(item["file_type"] == "txt" for item in res_txt.json()["items"])

    # 4. Search query
    res_search = await client.get("/api/v1/library?search=UniqueSearchTitle123")
    assert res_search.status_code == 200
    assert len(res_search.json()["items"]) >= 1
    assert res_search.json()["items"][0]["title"] == "UniqueSearchTitle123"


@pytest.mark.asyncio
async def test_get_and_update_material(client: AsyncClient):
    # Upload one
    files = {"file": ("update_me.txt", b"Vor dem Update", "text/plain")}
    create_res = await client.post(
        "/api/v1/library/upload",
        files=files,
        data={"title": "Original Title", "cefr_level": "A1", "topic": "General"}
    )
    mat_id = create_res.json()["id"]

    # Get single
    get_res = await client.get(f"/api/v1/library/{mat_id}")
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Original Title"

    # Update metadata
    update_res = await client.patch(
        f"/api/v1/library/{mat_id}",
        json={"title": "New Updated Title", "cefr_level": "B1", "topic": "Schreiben", "description": "Updated notes"}
    )
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["title"] == "New Updated Title"
    assert updated["cefr_level"] == "B1"
    assert updated["topic"] == "Schreiben"
    assert updated["description"] == "Updated notes"

    # Invalid level rejected
    bad_res = await client.patch(f"/api/v1/library/{mat_id}", json={"cefr_level": "INVALID"})
    assert bad_res.status_code == 400


@pytest.mark.asyncio
async def test_download_and_delete_material(client: AsyncClient):
    file_bytes = b"Content to test download and delete"
    files = {"file": ("download_test.txt", file_bytes, "text/plain")}
    create_res = await client.post("/api/v1/library/upload", files=files, data={"cefr_level": "A1"})
    mat_id = create_res.json()["id"]
    storage_name = create_res.json()["storage_filename"]

    # Verify physical file exists
    upload_path = Path(settings.UPLOAD_DIR) / storage_name
    assert upload_path.exists()

    # Download file
    down_res = await client.get(f"/api/v1/library/{mat_id}/file")
    assert down_res.status_code == 200
    assert down_res.content == file_bytes

    # Delete material
    del_res = await client.delete(f"/api/v1/library/{mat_id}")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Verify physical file removed
    assert not upload_path.exists()

    # Verify 404 on get after delete
    get_res = await client.get(f"/api/v1/library/{mat_id}")
    assert get_res.status_code == 404


@pytest.mark.asyncio
async def test_error_handling_invalid_ids_and_missing(client: AsyncClient):
    # Invalid ID format
    bad_id_res = await client.get("/api/v1/library/invalid-id-format")
    assert bad_id_res.status_code == 400
    assert "Invalid material ID format" in bad_id_res.json()["detail"]

    # Nonexistent valid ObjectId format
    non_existent_id = "507f1f77bcf86cd799439011"
    not_found_res = await client.get(f"/api/v1/library/{non_existent_id}")
    assert not_found_res.status_code == 404

    # Delete nonexistent material
    del_not_found = await client.delete(f"/api/v1/library/{non_existent_id}")
    assert del_not_found.status_code == 404

    # Update nonexistent material
    update_not_found = await client.patch(
        f"/api/v1/library/{non_existent_id}",
        json={"title": "Doesn't exist"}
    )
    assert update_not_found.status_code == 404


@pytest.mark.asyncio
async def test_download_link_resource_fails(client: AsyncClient):
    # Create a link resource (no physical file)
    link_res = await client.post(
        "/api/v1/library/links",
        json={"url": "https://example.com/german-guide", "title": "Web Guide"}
    )
    assert link_res.status_code == 201
    link_id = link_res.json()["id"]

    # Attempt to download physical file
    file_res = await client.get(f"/api/v1/library/{link_id}/file")
    assert file_res.status_code == 400
    assert "does not have an uploaded physical file" in file_res.json()["detail"]


@pytest.mark.asyncio
async def test_update_material_validation(client: AsyncClient):
    files = {"file": ("validation_test.txt", b"Inhalt", "text/plain")}
    res = await client.post("/api/v1/library/upload", files=files, data={"title": "Valid Initial"})
    mat_id = res.json()["id"]

    # Empty title should fail
    bad_title = await client.patch(f"/api/v1/library/{mat_id}", json={"title": "   "})
    assert bad_title.status_code == 400
    assert "Title cannot be empty" in bad_title.json()["detail"]
