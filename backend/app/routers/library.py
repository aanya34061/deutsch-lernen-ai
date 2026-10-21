from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Query, HTTPException, status
from fastapi.responses import FileResponse
from pymongo.errors import PyMongoError

from app.models.material import (
    MaterialResponse,
    MaterialUpdate,
    LearningLinkCreate,
    MaterialListResponse
)
from app.services.library_service import LibraryService

router = APIRouter(prefix="/library", tags=["Study Library"])

@router.post("/upload", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
async def upload_material(
    file: UploadFile = File(...),
    cefr_level: str = Form("A1"),
    topic: str = Form("General"),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None)
):
    """
    Upload German study material file (PDF, DOCX, TXT, JPG, PNG).
    Validates file format, size, sanitizes filename, extracts text, and indexes in database.
    """
    try:
        return await LibraryService.upload_file(
            file=file,
            cefr_level=cefr_level,
            topic=topic,
            title=title,
            description=description
        )
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
async def add_learning_link(link_data: LearningLinkCreate):
    """
    Add a German learning URL (YouTube video or web link).
    Fetches available captions or page text without bypassing restrictions.
    """
    try:
        return await LibraryService.add_learning_link(link_data)
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
            media_type=media_type
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
