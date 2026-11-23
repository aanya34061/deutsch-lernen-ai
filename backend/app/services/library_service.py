import os
import re
import uuid
import logging
import hashlib
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import UploadFile, HTTPException, status

from app.config import settings
from app.database import get_db
from app.security import current_user_id
from app.models.material import (
    MaterialResponse,
    MaterialUpdate,
    LearningLinkCreate,
    MaterialListResponse,
    SUPPORTED_CEFR_LEVELS,
    SUPPORTED_TOPICS,
)
from app.services.extractor_service import ExtractorService
from app.services.storage_service import ObjectStorage, StorageConfigurationError

logger = logging.getLogger("german_app.library")

ALLOWED_EXTENSIONS = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".txt": "txt",
    ".jpg": "image",
    ".jpeg": "image",
    ".png": "image",
    ".webp": "image",
    ".bmp": "image",
    ".tif": "image",
    ".tiff": "image",
    ".gif": "image",
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


def clean_extracted_text(value: Optional[str]) -> str:
    """Normalize extracted document text while retaining page markers and paragraphs."""
    text = (value or "").replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[^\S\n\t]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

class LibraryService:
    @staticmethod
    async def upload_file(
        file: UploadFile,
        cefr_level: str = "Unknown",
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
        supplied_type = (file.content_type or "").split(";")[0].strip().lower()
        allowed_types = {
            "pdf": {"application/pdf"},
            "docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/zip"},
            "txt": {"text/plain"},
            "image": {"image/jpeg", "image/png", "image/webp", "image/bmp", "image/tiff", "image/gif"},
        }
        if supplied_type and supplied_type != "application/octet-stream" and supplied_type not in allowed_types[file_type]:
            raise HTTPException(status_code=400, detail="The uploaded file type does not match its filename.")
        level_upper = cefr_level.title() if cefr_level and cefr_level.lower() == "unknown" else (cefr_level.upper() if cefr_level else "Unknown")
        if level_upper not in SUPPORTED_CEFR_LEVELS:
            level_upper = "Unknown"

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
        content_hasher = hashlib.sha256()
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
                    content_hasher.update(chunk)
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
        extracted_text = clean_extracted_text(extracted_info.get("text"))
        has_text = extracted_info.get("has_text", bool(extracted_text)) and bool(extracted_text)
        if not has_text:
            extracted_text = ""
        summary_text = extracted_info.get("summary") or f"{file_type.upper()} material: {safe_original_name}"
        error_msg = extracted_info.get("error") or (None if has_text else "No readable text could be extracted from this file.")

        material_title = title.strip() if title and title.strip() else Path(safe_original_name).stem

        # 5. Store file content outside the API host when object storage is enabled.
        now_iso = datetime.now(timezone.utc).isoformat()
        db = get_db()
        owner_id = current_user_id()
        upload_hash = content_hasher.hexdigest()
        duplicate = await db.materials.find_one({"user_id": owner_id, "upload_hash": upload_hash, "is_seeded": {"$ne": True}})
        if duplicate:
            destination_path.unlink(missing_ok=True)
            if duplicate.get("status") == "failed":
                retry_fields = {key: value for key, value in {
                    "extracted_text": extracted_text,
                    "summary": summary_text,
                    "status": "ready" if has_text and not error_msg else "failed",
                    "error_message": error_msg,
                    "processing_error": error_msg,
                    "chunks_count": 1 if extracted_text and not error_msg else 0,
                    "updated_at": now_iso,
                }.items()}
                retry_fields.update({"processing_status": "uploaded", "indexing_status": "not_indexed", "indexing_error": None})
                await db.materials.update_one({"_id": duplicate["_id"], "user_id": owner_id}, {"$set": retry_fields})
                duplicate.update(retry_fields)
                if extracted_text and not error_msg:
                    try:
                        from app.services.retrieval_service import RetrievalService
                        indexed = await RetrievalService.index_material(str(duplicate["_id"]))
                        retry_fields.update({
                            "indexing_status": indexed.get("status", "failed"),
                            "indexing_error": indexed.get("error"),
                            "chunks_count": indexed.get("chunks_count", 0),
                        })
                        await db.materials.update_one({"_id": duplicate["_id"], "user_id": owner_id}, {"$set": retry_fields})
                        duplicate.update(retry_fields)
                    except Exception as index_error:
                        logger.warning("Retry indexing failed for %s (%s).", duplicate["_id"], type(index_error).__name__)
            return MaterialResponse(**str_id(duplicate))

        use_object_storage = settings.STORAGE_PROVIDER.strip().lower() in {"s3", "r2", "s3-compatible"}
        material_oid = ObjectId()
        storage_key = f"{owner_id}/{material_oid}/{storage_filename}" if use_object_storage else None
        if use_object_storage:
            if not ObjectStorage.configured():
                destination_path.unlink(missing_ok=True)
                raise HTTPException(status_code=503, detail="Persistent file storage is not configured. Uploads are temporarily unavailable.")
            try:
                await ObjectStorage.upload_file(destination_path, storage_key, safe_original_name)
            except Exception as exc:
                destination_path.unlink(missing_ok=True)
                raise HTTPException(status_code=503, detail="Persistent file storage could not save this upload.") from exc

        material_doc = {
            "title": material_title,
            "original_filename": safe_original_name,
            "storage_filename": storage_filename,
            "file_path": None if use_object_storage else str(destination_path),
            "storage_key": storage_key,
            "storage_provider": "s3" if use_object_storage else "local",
            "file_type": file_type,
            "file_size": total_size,
            "source_type": "upload",
            "is_seeded": False,
            "user_id": owner_id,
            "upload_hash": upload_hash,
            "source_url": None,
            "cefr_level": level_upper,
            "topic": topic.strip() if topic and topic.strip() else "General",
            "description": description.strip() if description else None,
            "summary": summary_text,
            "extracted_text": extracted_text,
            "status": "ready" if has_text and not error_msg else "failed",
            "processing_status": "uploaded" if has_text and not error_msg else "failed",
            "processing_error": error_msg,
            "error_message": error_msg,
            "chunks_count": 1 if extracted_text and not error_msg else 0,
            "tags": [file_type, level_upper],
            "created_at": now_iso,
            "updated_at": now_iso
        }

        material_doc["_id"] = material_oid
        try:
            result = await db.materials.insert_one(material_doc)
        except Exception:
            # Do not leave a file behind when its metadata could not be persisted.
            try:
                destination_path.unlink(missing_ok=True)
            except OSError as cleanup_err:
                logger.warning("Could not remove unrecorded upload file: %s", cleanup_err)
            if storage_key:
                try:
                    await ObjectStorage.delete_file(storage_key)
                except Exception:
                    logger.error("Could not remove an unrecorded object-storage upload.")
            raise
        material_id_str = str(result.inserted_id)
        if use_object_storage:
            destination_path.unlink(missing_ok=True)
        material_doc["_id"] = material_id_str

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

        level_upper = link_data.cefr_level.title() if link_data.cefr_level and link_data.cefr_level.lower() == "unknown" else (link_data.cefr_level.upper() if link_data.cefr_level else "Unknown")
        if level_upper not in SUPPORTED_CEFR_LEVELS:
            level_upper = "Unknown"

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

        extracted_text = clean_extracted_text(extracted_info.get("text"))
        has_text = extracted_info.get("has_text", bool(extracted_text)) and bool(extracted_text)
        if not has_text:
            extracted_text = ""
        summary_text = extracted_info.get("summary") or f"Learning resource: {material_title}"
        error_msg = extracted_info.get("error") or (None if has_text else "No accessible text or transcript was extracted from this link.")

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
            "user_id": current_user_id(),
            "source_url": url,
            "cefr_level": level_upper,
            "topic": link_data.topic.strip() if link_data.topic and link_data.topic.strip() else "General",
            "description": link_data.description.strip() if link_data.description else None,
            "summary": summary_text,
            "extracted_text": extracted_text,
            "status": "ready" if has_text and not error_msg else "failed",
            "processing_status": "uploaded" if has_text and not error_msg else "failed",
            "processing_error": error_msg,
            "error_message": error_msg,
            "chunks_count": 1 if extracted_text and not error_msg else 0,
            "tags": [file_type, level_upper],
            "created_at": now_iso,
            "updated_at": now_iso
        }

        db = get_db()
        duplicate = await db.materials.find_one({"user_id": current_user_id(), "source_url": url, "is_seeded": {"$ne": True}})
        if duplicate:
            if duplicate.get("status") == "failed":
                retry_fields = {key: material_doc[key] for key in (
                    "title", "description", "extracted_text", "summary", "status", "error_message", "chunks_count", "updated_at"
                )}
                retry_fields["indexing_status"] = "not_indexed"
                retry_fields["indexing_error"] = None
                await db.materials.update_one({"_id": duplicate["_id"], "user_id": current_user_id()}, {"$set": retry_fields})
                if extracted_text and not error_msg:
                    try:
                        from app.services.retrieval_service import RetrievalService
                        index_res = await RetrievalService.index_material(str(duplicate["_id"]))
                        retry_fields["indexing_status"] = index_res.get("status", "failed")
                        retry_fields["indexing_error"] = index_res.get("error")
                        retry_fields["chunks_count"] = index_res.get("chunks_count", 0)
                    except Exception as idx_err:
                        retry_fields["indexing_status"] = "failed"
                        retry_fields["indexing_error"] = str(idx_err)
                        logger.warning("Retry indexing failed for %s: %s", duplicate["_id"], idx_err)
                    await db.materials.update_one({"_id": duplicate["_id"], "user_id": current_user_id()}, {"$set": retry_fields})
                duplicate.update(retry_fields)
            return MaterialResponse(**str_id(duplicate))
        result = await db.materials.insert_one(material_doc)
        material_id_str = str(result.inserted_id)
        material_doc["_id"] = material_id_str

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
            "user_id": current_user_id(),
            "is_seeded": {"$ne": True},
        }

        normalized_level = "Unknown" if level and level.lower() == "unknown" else (level.upper() if level else None)
        if normalized_level and normalized_level in SUPPORTED_CEFR_LEVELS:
            query["cefr_level"] = normalized_level
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
        doc = await db.materials.find_one({"_id": obj_id, "user_id": current_user_id(), "is_seeded": {"$ne": True}})
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
        doc = await db.materials.find_one({"_id": obj_id, "user_id": current_user_id(), "is_seeded": {"$ne": True}})
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
            lvl = "Unknown" if update_data.cefr_level.lower() == "unknown" else update_data.cefr_level.upper()
            if lvl not in SUPPORTED_CEFR_LEVELS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid CEFR level: {lvl}. Allowed: {SUPPORTED_CEFR_LEVELS}"
                )
            updates["cefr_level"] = lvl
            updates["level_manually_set"] = True
        if update_data.topic is not None:
            updates["topic"] = update_data.topic.strip() or "General"
        if update_data.description is not None:
            updates["description"] = update_data.description.strip()
        if update_data.tags is not None:
            updates["tags"] = update_data.tags

        updates["updated_at"] = datetime.now(timezone.utc).isoformat()

        await db.materials.update_one({"_id": obj_id, "user_id": current_user_id(), "is_seeded": {"$ne": True}}, {"$set": updates})

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

        updated_doc = await db.materials.find_one({"_id": obj_id, "user_id": current_user_id(), "is_seeded": {"$ne": True}})
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
        doc = await db.materials.find_one({"_id": obj_id, "user_id": current_user_id(), "is_seeded": {"$ne": True}})
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Material with ID {material_id} not found."
            )

        storage_key = doc.get("storage_key")
        if storage_key:
            await ObjectStorage.delete_file(storage_key)

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
        await db.materials.delete_one({"_id": obj_id, "user_id": current_user_id(), "is_seeded": {"$ne": True}})

        # Remove generated study artifacts so they cannot outlive their source.
        await db.study_notes.delete_many({"material_id": material_id, "user_id": current_user_id()})
        await db.exercises.delete_many({"material_id": material_id, "user_id": current_user_id(), "origin": "ai_generated"})

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
        doc = await db.materials.find_one({"_id": obj_id, "user_id": current_user_id(), "is_seeded": {"$ne": True}})
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Material with ID {material_id} not found."
            )

        storage_key = doc.get("storage_key")
        original_name = doc.get("original_filename") or doc.get("storage_filename") or "study-material"
        if storage_key:
            file_path = await ObjectStorage.download_to_temp(storage_key)
            media_type = mimetypes.guess_type(original_name)[0] or "application/octet-stream"
            return file_path, original_name, media_type

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
            ".png": "image/png",
            ".webp": "image/webp",
            ".bmp": "image/bmp",
            ".tif": "image/tiff",
            ".tiff": "image/tiff",
            ".gif": "image/gif",
        }
        media_type = media_types.get(ext, "application/octet-stream")
        return file_path, original_name, media_type

    @staticmethod
    async def get_material_file_download_url(material_id: str) -> tuple[str, str]:
        """Return a short-lived signed URL only after checking the material owner."""
        try:
            obj_id = ObjectId(material_id)
        except (InvalidId, ValueError):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid material ID format.")
        doc = await get_db().materials.find_one({
            "_id": obj_id, "user_id": current_user_id(), "is_seeded": {"$ne": True}
        })
        if not doc:
            raise HTTPException(status_code=404, detail="Material not found.")
        storage_key = doc.get("storage_key")
        if not storage_key:
            raise HTTPException(status_code=400, detail="This file is stored locally; use the authenticated file endpoint.")
        original_name = doc.get("original_filename") or "study-material"
        return await ObjectStorage.presigned_download_url(storage_key, original_name), original_name
