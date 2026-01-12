import logging
from typing import BinaryIO
from azure.storage.blob import BlobServiceClient, ContainerClient
from azure.core.exceptions import ResourceNotFoundError
from ..config import settings

logger = logging.getLogger(__name__)


class BlobStorageService:
    """Service for Azure Blob Storage operations."""

    def __init__(self):
        """Initialize Azure Blob Storage client."""
        self.blob_service_client = BlobServiceClient.from_connection_string(
            settings.azure_storage_connection_string
        )
        self.container_name = settings.azure_storage_container_name
        self._ensure_container_exists()

    def _ensure_container_exists(self):
        """Create container if it doesn't exist."""
        try:
            container_client = self.blob_service_client.get_container_client(
                self.container_name
            )
            container_client.get_container_properties()
            logger.info(f"Container '{self.container_name}' exists")
        except ResourceNotFoundError:
            container_client = self.blob_service_client.create_container(
                self.container_name
            )
            logger.info(f"Created container '{self.container_name}'")

    async def upload_pdf(
        self,
        file: BinaryIO,
        blob_name: str,
        metadata: dict = None
    ) -> str:
        """
        Upload PDF file to blob storage.

        Args:
            file: Binary file object
            blob_name: Name for the blob
            metadata: Optional metadata dict

        Returns:
            Blob URL
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )

            # Upload the file
            blob_client.upload_blob(
                file,
                overwrite=True,
                metadata=metadata or {}
            )

            blob_url = blob_client.url
            logger.info(f"Uploaded blob: {blob_name}")

            return blob_url

        except Exception as e:
            logger.error(f"Failed to upload blob {blob_name}: {str(e)}")
            raise

    async def download_pdf(self, blob_name: str) -> bytes:
        """
        Download PDF file from blob storage.

        Args:
            blob_name: Name of the blob

        Returns:
            File bytes
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )

            blob_data = blob_client.download_blob()
            content = blob_data.readall()

            logger.info(f"Downloaded blob: {blob_name}")
            return content

        except Exception as e:
            logger.error(f"Failed to download blob {blob_name}: {str(e)}")
            raise

    async def delete_pdf(self, blob_name: str) -> bool:
        """
        Delete PDF file from blob storage.

        Args:
            blob_name: Name of the blob

        Returns:
            True if deleted successfully
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )

            blob_client.delete_blob()
            logger.info(f"Deleted blob: {blob_name}")
            return True

        except ResourceNotFoundError:
            logger.warning(f"Blob not found: {blob_name}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete blob {blob_name}: {str(e)}")
            raise

    async def list_pdfs(self, prefix: str = None) -> list[str]:
        """
        List all PDFs in the container.

        Args:
            prefix: Optional prefix to filter blobs

        Returns:
            List of blob names
        """
        try:
            container_client = self.blob_service_client.get_container_client(
                self.container_name
            )

            blob_list = container_client.list_blobs(name_starts_with=prefix)
            blob_names = [blob.name for blob in blob_list]

            logger.info(f"Listed {len(blob_names)} blobs")
            return blob_names

        except Exception as e:
            logger.error(f"Failed to list blobs: {str(e)}")
            raise
