from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Query, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
from pymongo.errors import PyMongoError

from app.models.material import (
    MaterialResponse,
    MaterialUpdate,
    LearningLinkCreate,
    MaterialListResponse
)
from app.services.library_service import LibraryService, clean_extracted_text
from app.services.extractor_service import ExtractorService
from app.services.material_intelligence_service import MaterialIntelligenceService
from app.database import get_db
from bson import ObjectId

router = APIRouter(prefix="/library", tags=["Study Library"])

@router.post("/upload", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
async def upload_material(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    cefr_level: str = Form("Unknown"),
    topic: str = Form("General"),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None)
):
    """
    Upload German study material file (PDF, DOCX, TXT, JPG, PNG).
    Validates file format, size, sanitizes filename, extracts text, and indexes in database.
    """
    try:
        material = await LibraryService.upload_file(
            file=file,
            cefr_level=cefr_level,
            topic=topic,
            title=title,
            description=description
        )
        if material.status == "ready" and material.processing_status != "ready":
            background_tasks.add_task(MaterialIntelligenceService.process_material, material.id)
        return material
    except HTTPException:
        raise
    except (PyMongoError, RuntimeError) as db_err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable. The requested library change was not confirmed; please try again."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upload failed while processing the file. Please check the file and try again."
        )

@router.post("/links", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
async def add_learning_link(link_data: LearningLinkCreate, background_tasks: BackgroundTasks):
    """
    Add a German learning URL (YouTube video or web link).
    Fetches available captions or page text without bypassing restrictions.
    """
    try:
        material = await LibraryService.add_learning_link(link_data)
        if material.status == "ready" and material.processing_status != "ready":
            background_tasks.add_task(MaterialIntelligenceService.process_material, material.id)
        return material
    except HTTPException:
        raise
    except (PyMongoError, RuntimeError) as db_err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable. The requested library change was not confirmed; please try again."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process the learning link. Please check the URL and try again."
        )

@router.get("", response_model=MaterialListResponse)
async def list_materials(
    level: Optional[str] = Query(None, description="Filter by CEFR level (A1-C2)"),
    topic: Optional[str] = Query(None, description="Filter by topic (e.g., Grammar, Vocabulary)"),
    file_type: Optional[str] = Query(None, description="Filter by material type (pdf, docx, txt, image, youtube, link)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by processing status (uploaded, processing, ready, failed)"),
    search: Optional[str] = Query(None, description="Search term in title, description, topic, text"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200)
):
    """List study materials with optional filtering, search, and pagination."""
    try:
        return await LibraryService.list_materials(
            level=level,
            topic=topic,
            file_type=file_type,
            status_filter=status_filter,
            search=search,
            skip=skip,
            limit=limit
        )
    except (PyMongoError, RuntimeError) as db_err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable. Could not load library materials; please try again."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not load library materials. Please try again."
        )

@router.get("/{material_id}", response_model=MaterialResponse)
async def get_material(material_id: str):
    """Retrieve details and extracted text of a single study material."""
    try:
        return await LibraryService.get_material(material_id)
    except HTTPException:
        raise
    except (PyMongoError, RuntimeError) as db_err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable. Could not retrieve this material; please try again."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve this material. Please try again."
        )

@router.patch("/{material_id}", response_model=MaterialResponse)
@router.put("/{material_id}", response_model=MaterialResponse)
async def update_material(material_id: str, update_data: MaterialUpdate):
    """Update material classification, level, topic, title, description, or tags."""
    try:
        return await LibraryService.update_material(material_id, update_data)
    except HTTPException:
        raise
    except (PyMongoError, RuntimeError) as db_err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable. The material update was not confirmed; please try again."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update this material. Please try again."
        )

@router.delete("/{material_id}")
async def delete_material(material_id: str):
    """Delete study material metadata and remove associated local file."""
    try:
        return await LibraryService.delete_material(material_id)
    except HTTPException:
        raise
    except (PyMongoError, RuntimeError) as db_err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable. The material deletion was not confirmed; please try again."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not delete this material. Please try again."
        )

@router.get("/{material_id}/file")
async def get_material_file(material_id: str):
    """Download or view the uploaded physical file."""
    try:
        file_path, original_filename, media_type = await LibraryService.get_material_file(material_id)
        return FileResponse(
            path=str(file_path),
            filename=original_filename,
            media_type=media_type,
            content_disposition_type="inline",
        )
    except HTTPException:
        raise
    except (PyMongoError, RuntimeError) as db_err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable. Could not retrieve this file; please try again."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve this file. Please try again."
        )

@router.post("/{material_id}/process/retry")
async def retry_material_processing(material_id: str, background_tasks: BackgroundTasks):
    """Retry OCR when needed, then AI analysis, notes, questions, and indexing."""
    material = await LibraryService.get_material(material_id)
    if material.file_type == "image" and not (material.extracted_text or "").strip():
        file_path, _, _ = await LibraryService.get_material_file(material_id)
        extracted_info = ExtractorService.extract_file_content(str(file_path), "image")
        extracted_text = clean_extracted_text(extracted_info.get("text"))
        if not extracted_text:
            error = extracted_info.get("error") or "OCR found no readable text in this image."
            await get_db().materials.update_one(
                {"_id": ObjectId(material_id), "user_id": "default", "is_seeded": {"$ne": True}},
                {"$set": {"status": "failed", "error_message": error, "processing_error": error}},
            )
            raise HTTPException(status_code=422, detail=error)

        await get_db().materials.update_one(
            {"_id": ObjectId(material_id), "user_id": "default", "is_seeded": {"$ne": True}},
            {"$set": {
                "extracted_text": extracted_text,
                "summary": extracted_info.get("summary"),
                "status": "ready",
                "error_message": None,
                "processing_status": "uploaded",
                "processing_error": None,
                "indexing_status": "not_indexed",
                "indexing_error": None,
                "chunks_count": 0,
            }},
        )
        material.status = "ready"
        material.extracted_text = extracted_text

    if material.status != "ready" or not (material.extracted_text or "").strip():
        raise HTTPException(status_code=409, detail=material.error_message or "This source has no readable extracted text to process.")
    oid = ObjectId(material_id)
    await get_db().materials.update_one(
        {"_id": oid, "user_id": "default", "is_seeded": {"$ne": True}},
        {"$set": {"processing_status": "uploaded", "processing_error": None}},
    )
    background_tasks.add_task(MaterialIntelligenceService.process_material, material_id, True)
    return {"status": "queued", "material_id": material_id}
