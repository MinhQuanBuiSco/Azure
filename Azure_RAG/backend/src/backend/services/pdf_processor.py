import logging
import re
from typing import BinaryIO
from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ..config import settings

logger = logging.getLogger(__name__)


class PDFProcessingService:
    """Service for processing PDF files into chunks."""

    def __init__(self):
        """Initialize the text splitter."""
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def extract_text_from_pdf(self, pdf_file: BinaryIO) -> tuple[str, dict]:
        """
        Extract text content from a PDF file.

        Args:
            pdf_file: Binary file object of the PDF

        Returns:
            Tuple of (full_text, metadata)
        """
        try:
            reader = PdfReader(pdf_file)
            total_pages = len(reader.pages)

            # Extract metadata
            metadata = {
                "total_pages": total_pages,
                "author": reader.metadata.get("/Author", "") if reader.metadata else "",
                "title": reader.metadata.get("/Title", "") if reader.metadata else "",
                "subject": reader.metadata.get("/Subject", "") if reader.metadata else "",
                "creator": reader.metadata.get("/Creator", "") if reader.metadata else "",
            }

            # Extract text from all pages
            full_text = ""
            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                if text:
                    full_text += f"\n--- Page {page_num} ---\n{text}\n"

            logger.info(f"Extracted {len(full_text)} characters from {total_pages} pages")

            return full_text, metadata

        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {str(e)}")
            raise ValueError(f"PDF processing failed: {str(e)}")

    def _extract_page_numbers(self, content: str) -> list[int]:
        """
        Extract page numbers from chunk content.

        Args:
            content: Chunk content that may contain page markers

        Returns:
            List of page numbers found in the content
        """
        # Find all page markers in the format "--- Page {num} ---"
        page_pattern = r"---\s*Page\s+(\d+)\s*---"
        matches = re.findall(page_pattern, content)

        if matches:
            return sorted(set(int(page) for page in matches))

        # If no page markers found, return empty list
        return []

    def chunk_text(self, text: str, document_metadata: dict) -> list[dict]:
        """
        Split text into chunks with metadata.

        Args:
            text: Full text to chunk
            document_metadata: Document-level metadata

        Returns:
            List of chunk dictionaries with text and metadata
        """
        try:
            # Split text into chunks
            chunks = self.text_splitter.create_documents(
                texts=[text],
                metadatas=[document_metadata]
            )

            # Convert to list of dicts with additional metadata
            chunk_list = []
            for i, chunk in enumerate(chunks):
                # Extract page numbers from chunk content
                page_numbers = self._extract_page_numbers(chunk.page_content)

                chunk_dict = {
                    "chunk_index": i,
                    "content": chunk.page_content,
                    "metadata": {
                        **chunk.metadata,
                        "chunk_id": f"{document_metadata.get('document_id', '')}_{i}",
                        "total_chunks": len(chunks),
                        "page_numbers": page_numbers
                    }
                }
                chunk_list.append(chunk_dict)

            logger.info(f"Created {len(chunk_list)} chunks from text")

            return chunk_list

        except Exception as e:
            logger.error(f"Failed to chunk text: {str(e)}")
            raise ValueError(f"Text chunking failed: {str(e)}")

    def process_pdf(
        self,
        pdf_file: BinaryIO,
        document_id: str,
        filename: str
    ) -> tuple[list[dict], dict]:
        """
        Complete PDF processing pipeline.

        Args:
            pdf_file: Binary PDF file
            document_id: Unique document identifier
            filename: Original filename

        Returns:
            Tuple of (chunks_list, document_metadata)
        """
        # Extract text and metadata
        full_text, pdf_metadata = self.extract_text_from_pdf(pdf_file)

        # Build document metadata
        document_metadata = {
            "document_id": document_id,
            "filename": filename,
            **pdf_metadata
        }

        # Chunk the text
        chunks = self.chunk_text(full_text, document_metadata)

        logger.info(f"Processed PDF '{filename}': {len(chunks)} chunks created")

        return chunks, document_metadata

    def estimate_chunks(self, text_length: int) -> int:
        """Estimate number of chunks for a given text length."""
        return max(1, text_length // (settings.chunk_size - settings.chunk_overlap))
