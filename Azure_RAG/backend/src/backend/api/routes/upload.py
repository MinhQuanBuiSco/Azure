import logging
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from ...models.schemas import UploadResponse
from ...services import BlobStorageService
from ...config import settings
from ..dependencies import get_blob_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    blob_service: BlobStorageService = Depends(get_blob_service)
):
    """
    Upload a PDF file to Azure Blob Storage.

    Args:
        file: PDF file to upload

    Returns:
        Upload response with document ID and blob URL
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Validate file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    max_size = settings.max_file_size_mb * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum of {settings.max_file_size_mb}MB"
        )

    try:
        # Generate unique document ID
        document_id = str(uuid.uuid4())

        # Create blob name
        blob_name = f"{document_id}/{file.filename}"

        # Upload to blob storage
        blob_url = await blob_service.upload_pdf(
            file=file.file,
            blob_name=blob_name,
            metadata={
                "document_id": document_id,
                "original_filename": file.filename,
                "content_type": file.content_type
            }
        )

        logger.info(f"Uploaded file {file.filename} as document {document_id}")

        return UploadResponse(
            document_id=document_id,
            filename=file.filename,
            size_bytes=file_size,
            blob_url=blob_url
        )

    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
