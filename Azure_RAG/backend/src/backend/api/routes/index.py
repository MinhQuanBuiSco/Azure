import logging
import io
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from ...models.schemas import IndexRequest, IndexingProgress, IndexingStatus
from ...services import (
    BlobStorageService,
    PDFProcessingService,
    EntityExtractionService,
    EmbeddingService,
    SearchService,
    cache_service
)
from ..dependencies import get_blob_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/index", tags=["indexing"])


async def process_and_index_document(document_id: str, filename: str, extract_entities: bool = True):
    """
    Background task to process and index a document.

    Args:
        document_id: Unique document identifier
        filename: Original filename
        extract_entities: Whether to extract entities
    """
    # Initialize services (lazy instantiation for background task)
    blob_service = BlobStorageService()
    pdf_service = PDFProcessingService()
    entity_service = EntityExtractionService()
    embedding_service = EmbeddingService()
    search_service = SearchService()

    try:
        # Update status: Processing
        await cache_service.set_indexing_status(
            document_id,
            {
                "document_id": document_id,
                "status": IndexingStatus.PROCESSING.value,
                "progress_percentage": 10,
                "current_step": "Downloading PDF from blob storage"
            }
        )

        # Download PDF from blob
        blob_name = f"{document_id}/{filename}"
        pdf_bytes = await blob_service.download_pdf(blob_name)
        pdf_file = io.BytesIO(pdf_bytes)

        # Process PDF
        await cache_service.set_indexing_status(
            document_id,
            {
                "document_id": document_id,
                "status": IndexingStatus.PROCESSING.value,
                "progress_percentage": 20,
                "current_step": "Extracting text and chunking PDF"
            }
        )

        chunks, doc_metadata = pdf_service.process_pdf(pdf_file, document_id, filename)
        total_chunks = len(chunks)

        logger.info(f"Processing document {document_id}: {total_chunks} chunks")

        # Extract entities if enabled
        entities_list = []
        if extract_entities:
            await cache_service.set_indexing_status(
                document_id,
                {
                    "document_id": document_id,
                    "status": IndexingStatus.EXTRACTING_ENTITIES.value,
                    "progress_percentage": 40,
                    "current_step": f"Extracting entities from {total_chunks} chunks",
                    "total_chunks": total_chunks
                }
            )

            # Extract entities for each chunk
            for i, chunk in enumerate(chunks):
                entities = await entity_service.extract_entities(
                    text=chunk["content"],
                    context=f"{filename} - Chunk {i+1}/{total_chunks}"
                )
                entities_list.append(entities)

                # Update progress
                if (i + 1) % 5 == 0:  # Update every 5 chunks
                    await cache_service.set_indexing_status(
                        document_id,
                        {
                            "document_id": document_id,
                            "status": IndexingStatus.EXTRACTING_ENTITIES.value,
                            "progress_percentage": 40 + int((i + 1) / total_chunks * 20),
                            "current_step": f"Extracted entities from {i+1}/{total_chunks} chunks",
                            "total_chunks": total_chunks,
                            "processed_chunks": i + 1
                        }
                    )

            logger.info(f"Extracted entities from {total_chunks} chunks")
        else:
            # Empty entities if not extracting
            from ...models.entities import ExtractedEntities
            entities_list = [ExtractedEntities() for _ in chunks]

        # Generate embeddings
        await cache_service.set_indexing_status(
            document_id,
            {
                "document_id": document_id,
                "status": IndexingStatus.EMBEDDING.value,
                "progress_percentage": 60,
                "current_step": f"Generating embeddings for {total_chunks} chunks"
            }
        )

        chunk_texts = [chunk["content"] for chunk in chunks]
        embeddings = await embedding_service.create_embeddings_batch(chunk_texts)

        logger.info(f"Generated {len(embeddings)} embeddings")

        # Index to Azure AI Search
        await cache_service.set_indexing_status(
            document_id,
            {
                "document_id": document_id,
                "status": IndexingStatus.INDEXING.value,
                "progress_percentage": 80,
                "current_step": "Indexing to Azure AI Search"
            }
        )

        await search_service.index_document_chunks(chunks, embeddings, entities_list)

        # Completed
        await cache_service.set_indexing_status(
            document_id,
            {
                "document_id": document_id,
                "status": IndexingStatus.COMPLETED.value,
                "progress_percentage": 100,
                "current_step": "Indexing completed successfully",
                "total_chunks": total_chunks,
                "processed_chunks": total_chunks,
                "entities_extracted": sum(not e.is_empty() for e in entities_list)
            }
        )

        logger.info(f"Successfully indexed document {document_id}")

    except Exception as e:
        logger.error(f"Indexing failed for document {document_id}: {str(e)}")

        # Update status: Failed
        await cache_service.set_indexing_status(
            document_id,
            {
                "document_id": document_id,
                "status": IndexingStatus.FAILED.value,
                "progress_percentage": 0,
                "current_step": "Indexing failed",
                "error_message": str(e)
            }
        )


@router.post("/{document_id}", response_model=IndexingProgress)
async def start_indexing(
    document_id: str,
    background_tasks: BackgroundTasks,
    request: IndexRequest = None,
    blob_service: BlobStorageService = Depends(get_blob_service)
):
    """
    Start indexing a document in the background.

    Args:
        document_id: Document ID from upload
        background_tasks: FastAPI background tasks
        request: Optional indexing configuration

    Returns:
        Initial indexing progress
    """
    try:
        # Check if document exists in blob storage
        blobs = await blob_service.list_pdfs(prefix=document_id)
        if not blobs:
            raise HTTPException(status_code=404, detail="Document not found")

        filename = blobs[0].split("/")[-1]  # Extract filename from blob path

        extract_entities = request.extract_entities if request else True

        # Set initial status
        await cache_service.set_indexing_status(
            document_id,
            {
                "document_id": document_id,
                "status": IndexingStatus.PENDING.value,
                "progress_percentage": 0,
                "current_step": "Queued for processing"
            }
        )

        # Start background processing
        background_tasks.add_task(
            process_and_index_document,
            document_id,
            filename,
            extract_entities
        )

        logger.info(f"Started indexing for document {document_id}")

        return IndexingProgress(
            document_id=document_id,
            status=IndexingStatus.PENDING,
            progress_percentage=0,
            current_step="Indexing started"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start indexing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}", response_model=IndexingProgress)
async def get_indexing_status(document_id: str):
    """
    Get the current indexing status for a document.

    Args:
        document_id: Document ID

    Returns:
        Current indexing progress
    """
    try:
        status = await cache_service.get_indexing_status(document_id)

        if not status:
            # Return "not started" status instead of 404 to avoid frontend errors
            return IndexingProgress(
                document_id=document_id,
                status=IndexingStatus.PENDING,
                progress_percentage=0,
                current_step="Indexing not started. Click 'Start Indexing' to begin."
            )

        return IndexingProgress(**status)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get indexing status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
