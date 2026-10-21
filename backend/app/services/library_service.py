import os
import re
import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import UploadFile, HTTPException, status

from app.config import settings
from app.database import get_db
from app.models.material import (
    MaterialResponse,
    MaterialUpdate,
    LearningLinkCreate,
    MaterialListResponse,
    SUPPORTED_CEFR_LEVELS,
    SUPPORTED_TOPICS,
)
from app.services.extractor_service import ExtractorService

logger = logging.getLogger("german_app.library")

# These titles came from the original demo Library seed. Keep this exact list in
# the backend query as a guard in case startup labeling could not run.
LEGACY_DEMO_MATERIAL_TITLES = (
    "A1 Begrüßungen und Vorstellungen (Greetings Guide)",
    "Deutsche Artikel im Alltag (Articles in Daily Life)",
    "Im Café bestellen (Ordering in a German Café)",
)

ALLOWED_EXTENSIONS = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".txt": "txt",
    ".jpg": "image",
    ".jpeg": "image",
    ".png": "image",
}

def str_id(doc: dict) -> dict:
    """Convert MongoDB ObjectId _id to string."""
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

def sanitize_filename(filename: str) -> str:
    """Strip path components and remove potentially dangerous characters."""
    # Strip any directory paths
    base = Path(filename).name
    # Keep alphanumeric, dot, underscore, dash, and spaces
    safe = re.sub(r"[^\w\s\.-]", "_", base)
    # Prevent hidden files or double dots
    safe = safe.lstrip(".")
    return safe or "unnamed_file"

def get_upload_dir() -> Path:
    """Return resolved UPLOAD_DIR Path and ensure it exists."""
    upload_path = Path(settings.UPLOAD_DIR).resolve()
    upload_path.mkdir(parents=True, exist_ok=True)
    return upload_path


def is_within_upload_dir(path: Path, upload_dir: Path) -> bool:
    """Return whether a resolved path is inside the configured upload directory."""
    try:
        path.resolve().relative_to(upload_dir.resolve())
        return True
    except ValueError:
        return False

class LibraryService:
    @staticmethod
    async def upload_file(
        file: UploadFile,
        cefr_level: str = "A1",
        topic: str = "General",
        title: Optional[str] = None,
        description: Optional[str] = None
    ) -> MaterialResponse:
        """Process, validate, save and extract text from an uploaded study file."""
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file must have a filename."
            )

        # 1. Validate file extension
        safe_original_name = sanitize_filename(file.filename)
        ext = Path(safe_original_name).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            allowed_list = ", ".join(sorted(ALLOWED_EXTENSIONS.keys()))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type '{ext}'. Supported formats: {allowed_list} (PDF, DOCX, TXT, JPG, PNG)."
            )

        file_type = ALLOWED_EXTENSIONS[ext]
        level_upper = cefr_level.upper() if cefr_level else "A1"
        if level_upper not in SUPPORTED_CEFR_LEVELS:
            level_upper = "A1"

        # 2. Prevent path traversal and generate unique secure storage filename
        unique_prefix = uuid.uuid4().hex
        storage_filename = f"{unique_prefix}_{safe_original_name}"
        upload_dir = get_upload_dir()
        destination_path = (upload_dir / storage_filename).resolve()

        # Path traversal guard
        if not is_within_upload_dir(destination_path, upload_dir):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file path detected."
            )

        # 3. Stream file to disk and validate size limit
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        total_size = 0
        try:
            with open(destination_path, "wb") as f:
                while chunk := await file.read(1024 * 1024):  # 1MB chunks
                    total_size += len(chunk)
                    if total_size > max_bytes:
                        # Clean up partial file
                        f.close()
                        if destination_path.exists():
                            destination_path.unlink()
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
                        )
                    f.write(chunk)
        except HTTPException:
            raise
        except Exception:
            if destination_path.exists():
                destination_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save the uploaded file. Please try again."
            )

        # 4. Extract text based on file format
        extracted_info = ExtractorService.extract_file_content(str(destination_path), file_type)
        extracted_text = extracted_info.get("text", "")
        summary_text = extracted_info.get("summary") or f"{file_type.upper()} material: {safe_original_name}"
        error_msg = extracted_info.get("error")

        material_title = title.strip() if title and title.strip() else Path(safe_original_name).stem

        # 5. Save metadata in MongoDB
        now_iso = datetime.now(timezone.utc).isoformat()
        material_doc = {
            "title": material_title,
            "original_filename": safe_original_name,
            "storage_filename": storage_filename,
            "file_path": str(destination_path),
            "file_type": file_type,
            "file_size": total_size,
            "source_type": "upload",
            "is_seeded": False,
            "source_url": None,
            "cefr_level": level_upper,
            "topic": topic.strip() if topic and topic.strip() else "General",
            "description": description.strip() if description else None,
            "summary": summary_text,
            "extracted_text": extracted_text,
            "status": "ready" if not error_msg else "failed",
            "error_message": error_msg,
            "chunks_count": 1 if extracted_text and not error_msg else 0,
            "tags": [file_type, level_upper],
            "created_at": now_iso,
            "updated_at": now_iso
        }

        db = get_db()
        try:
            result = await db.materials.insert_one(material_doc)
        except Exception:
            # Do not leave a file behind when its metadata could not be persisted.
            try:
                destination_path.unlink(missing_ok=True)
            except OSError as cleanup_err:
                logger.warning("Could not remove unrecorded upload file: %s", cleanup_err)
            raise
        material_id_str = str(result.inserted_id)
        material_doc["_id"] = material_id_str

        # Phase 4: Index material chunks into knowledge_chunks collection
        if extracted_text and not error_msg:
            try:
                from app.services.retrieval_service import RetrievalService
                index_res = await RetrievalService.index_material(material_id_str)
                material_doc["indexing_status"] = index_res.get("status", "indexed")
                material_doc["chunks_count"] = index_res.get("chunks_count", 1)
            except Exception as idx_err:
                logger.warning(f"Background indexing error for {material_id_str}: {idx_err}")

        return MaterialResponse(**material_doc)

    @staticmethod
    async def add_learning_link(link_data: LearningLinkCreate) -> MaterialResponse:
        """Process, validate, save and extract captions/text from YouTube or learning URLs."""
        url = link_data.url.strip()
        if not url.startswith(("http://", "https://")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="URL must start with http:// or https://"
            )

        level_upper = link_data.cefr_level.upper() if link_data.cefr_level else "A1"
        if level_upper not in SUPPORTED_CEFR_LEVELS:
            level_upper = "A1"

        is_youtube = bool(ExtractorService.parse_youtube_video_id(url))
        file_type = "youtube" if is_youtube else "link"

        if is_youtube:
            extracted_info = await ExtractorService.extract_from_youtube(url)
        else:
            extracted_info = await ExtractorService.extract_from_web_url(url)

        inferred_title = extracted_info.get("title")
        material_title = (
            link_data.title.strip() if link_data.title and link_data.title.strip()
            else (inferred_title or ("YouTube Video" if is_youtube else url))
        )

        extracted_text = extracted_info.get("text", "")
        summary_text = extracted_info.get("summary") or f"Learning resource: {material_title}"
        error_msg = extracted_info.get("error")

        now_iso = datetime.now(timezone.utc).isoformat()
        material_doc = {
            "title": material_title,
            "original_filename": None,
            "storage_filename": None,
            "file_path": None,
            "file_type": file_type,
            "file_size": 0,
            "source_type": "link",
            "is_seeded": False,
            "source_url": url,
            "cefr_level": level_upper,
            "topic": link_data.topic.strip() if link_data.topic and link_data.topic.strip() else "General",
            "description": link_data.description.strip() if link_data.description else None,
            "summary": summary_text,
            "extracted_text": extracted_text,
            "status": "ready" if not error_msg else "failed",
            "error_message": error_msg,
            "chunks_count": 1 if extracted_text and not error_msg else 0,
            "tags": [file_type, level_upper],
            "created_at": now_iso,
            "updated_at": now_iso
        }

        db = get_db()
        result = await db.materials.insert_one(material_doc)
        material_id_str = str(result.inserted_id)
        material_doc["_id"] = material_id_str

        # Phase 4: Index material chunks into knowledge_chunks collection
        if extracted_text and not error_msg:
            try:
                from app.services.retrieval_service import RetrievalService
                index_res = await RetrievalService.index_material(material_id_str)
                material_doc["indexing_status"] = index_res.get("status", "indexed")
                material_doc["chunks_count"] = index_res.get("chunks_count", 1)
            except Exception as idx_err:
                logger.warning(f"Background indexing error for {material_id_str}: {idx_err}")

        return MaterialResponse(**material_doc)

    @staticmethod
    async def list_materials(
        level: Optional[str] = None,
        topic: Optional[str] = None,
        file_type: Optional[str] = None,
        status_filter: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> MaterialListResponse:
        """Query materials with optional filters, search, and pagination."""
        db = get_db()
        query: Dict[str, Any] = {
            "is_seeded": {"$ne": True},
            "title": {"$nin": list(LEGACY_DEMO_MATERIAL_TITLES)},
        }

        if level and level.upper() in SUPPORTED_CEFR_LEVELS:
            query["cefr_level"] = level.upper()
        if topic and topic.strip():
            query["topic"] = {"$regex": f"^{re.escape(topic.strip())}$", "$options": "i"}
        if file_type and file_type.strip():
            query["file_type"] = file_type.strip().lower()
        if status_filter and status_filter.strip():
            query["status"] = status_filter.strip().lower()

        if search and search.strip():
            search_regex = {"$regex": re.escape(search.strip()), "$options": "i"}
            query["$or"] = [
                {"title": search_regex},
                {"description": search_regex},
                {"topic": search_regex},
                {"extracted_text": search_regex},
                {"original_filename": search_regex}
            ]

        total = await db.materials.count_documents(query)
        cursor = db.materials.find(query).sort("_id", -1).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)

        items = [MaterialResponse(**str_id(doc)) for doc in docs]
        return MaterialListResponse(items=items, total=total, page=(skip // limit) + 1 if limit else 1, limit=limit)

    @staticmethod
    async def get_material(material_id: str) -> MaterialResponse:
        """Retrieve a single material by ID."""
        try:
            obj_id = ObjectId(material_id)
        except (InvalidId, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid material ID format: {material_id}"
            )

        db = get_db()
        doc = await db.materials.find_one({"_id": obj_id})
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Material with ID {material_id} not found."
            )
        return MaterialResponse(**str_id(doc))

    @staticmethod
    async def update_material(material_id: str, update_data: MaterialUpdate) -> MaterialResponse:
        """Update material metadata (cefr_level, topic, title, description, tags)."""
        try:
            obj_id = ObjectId(material_id)
        except (InvalidId, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid material ID format: {material_id}"
            )

        db = get_db()
        doc = await db.materials.find_one({"_id": obj_id})
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Material with ID {material_id} not found."
            )

        updates: Dict[str, Any] = {}
        if update_data.title is not None:
            if not update_data.title.strip():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title cannot be empty.")
            updates["title"] = update_data.title.strip()
        if update_data.cefr_level is not None:
            lvl = update_data.cefr_level.upper()
            if lvl not in SUPPORTED_CEFR_LEVELS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid CEFR level: {lvl}. Allowed: {SUPPORTED_CEFR_LEVELS}"
                )
            updates["cefr_level"] = lvl
        if update_data.topic is not None:
            updates["topic"] = update_data.topic.strip() or "General"
        if update_data.description is not None:
            updates["description"] = update_data.description.strip()
        if update_data.tags is not None:
            updates["tags"] = update_data.tags

        updates["updated_at"] = datetime.now(timezone.utc).isoformat()

        await db.materials.update_one({"_id": obj_id}, {"$set": updates})

        # Phase 4: Synchronize chunk metadata if level, topic or title changed
        try:
            from app.services.retrieval_service import RetrievalService
            await RetrievalService.update_material_metadata_in_chunks(
                material_id=material_id,
                title=updates.get("title"),
                cefr_level=updates.get("cefr_level"),
                topic=updates.get("topic")
            )
        except Exception as chunk_err:
            logger.warning(f"Could not update chunks metadata: {chunk_err}")

        updated_doc = await db.materials.find_one({"_id": obj_id})
        return MaterialResponse(**str_id(updated_doc))

    @staticmethod
    async def delete_material(material_id: str) -> dict:
        """Delete material metadata and remove associated local file."""
        try:
            obj_id = ObjectId(material_id)
        except (InvalidId, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid material ID format: {material_id}"
            )

        db = get_db()
        doc = await db.materials.find_one({"_id": obj_id})
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Material with ID {material_id} not found."
            )

        # Remove local file if present and safe
        storage_filename = doc.get("storage_filename")
        if storage_filename:
            upload_dir = get_upload_dir()
            file_path = (upload_dir / storage_filename).resolve()
            if is_within_upload_dir(file_path, upload_dir) and file_path.exists():
                try:
                    file_path.unlink()
                    logger.info(f"Deleted local file: {file_path}")
                except Exception as file_err:
                    logger.warning(f"Could not delete local file {file_path}: {file_err}")

        # Delete database record
        await db.materials.delete_one({"_id": obj_id})

        # Phase 4: Clean up indexed chunks in knowledge_chunks collection
        try:
            from app.services.retrieval_service import RetrievalService
            await RetrievalService.delete_material_chunks(material_id)
        except Exception as chunk_err:
            logger.warning(f"Could not delete chunks for material {material_id}: {chunk_err}")

        return {
            "success": True,
            "message": f"Material '{doc.get('title')}' deleted successfully.",
            "deleted_id": material_id
        }

    @staticmethod
    async def get_material_file(material_id: str) -> tuple[Path, str, str]:
        """Verify and return (file_path, original_filename, media_type) for download."""
        try:
            obj_id = ObjectId(material_id)
        except (InvalidId, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid material ID format: {material_id}"
            )

        db = get_db()
        doc = await db.materials.find_one({"_id": obj_id})
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Material with ID {material_id} not found."
            )

        storage_filename = doc.get("storage_filename")
        if not storage_filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This material does not have an uploaded physical file."
            )

        upload_dir = get_upload_dir()
        file_path = (upload_dir / storage_filename).resolve()
        if not is_within_upload_dir(file_path, upload_dir) or not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found on local storage."
            )

        original_name = doc.get("original_filename") or storage_filename
        ext = file_path.suffix.lower()
        media_types = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".txt": "text/plain",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png"
        }
        media_type = media_types.get(ext, "application/octet-stream")
        return file_path, original_name, media_type
