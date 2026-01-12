import logging
from openai import AzureOpenAI
from typing import List
from ..config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings using Azure OpenAI."""

    def __init__(self):
        """Initialize Azure OpenAI client."""
        self.client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint
        )
        self.deployment = settings.azure_openai_embedding_deployment
        self.dimensions = settings.azure_openai_embedding_dimensions

    async def create_embedding(self, text: str) -> List[float]:
        """
        Create embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.deployment
            )

            embedding = response.data[0].embedding
            logger.debug(f"Created embedding for text of length {len(text)}")

            return embedding

        except Exception as e:
            logger.error(f"Failed to create embedding: {str(e)}")
            raise

    async def create_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 16
    ) -> List[List[float]]:
        """
        Create embeddings for multiple texts in batches.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts per batch (max 16 for OpenAI)

        Returns:
            List of embedding vectors
        """
        all_embeddings = []

        try:
            # Process in batches
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]

                response = self.client.embeddings.create(
                    input=batch,
                    model=self.deployment
                )

                # Extract embeddings in order
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)

                logger.debug(f"Created embeddings for batch {i//batch_size + 1}")

            logger.info(f"Created {len(all_embeddings)} embeddings in total")

            return all_embeddings

        except Exception as e:
            logger.error(f"Failed to create batch embeddings: {str(e)}")
            raise

    async def create_query_embedding(self, query: str) -> List[float]:
        """
        Create embedding specifically for a search query.

        Args:
            query: Search query text

        Returns:
            Query embedding vector
        """
        # For search queries, we might want to add a prefix
        # But for now, just use the standard embedding
        return await self.create_embedding(query)

    def get_embedding_dimensions(self) -> int:
        """Get the dimensions of the embedding model."""
        return self.dimensions
