import logging
from openai import AzureOpenAI
from typing import Optional
from ..models.entities import ExtractedEntities
from ..config import settings

logger = logging.getLogger(__name__)


class EntityExtractionService:
    """Service for extracting entities from text using GPT-4o-mini structured outputs."""

    def __init__(self):
        """Initialize the Azure OpenAI client."""
        self.client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint
        )
        self.deployment = settings.azure_openai_chat_deployment

    async def extract_entities(self, text: str, context: Optional[str] = None) -> ExtractedEntities:
        """
        Extract entities from text using GPT-4o-mini structured outputs.

        Args:
            text: The text to extract entities from
            context: Optional context (e.g., document title, metadata)

        Returns:
            ExtractedEntities model with all extracted entities
        """
        try:
            # Build the prompt
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(text, context)

            # Call GPT-4o-mini with structured outputs
            response = self.client.beta.chat.completions.parse(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format=ExtractedEntities,
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=800
            )

            # Extract the structured response
            entities = response.choices[0].message.parsed

            logger.info(f"Extracted entities: {len(entities.people)} people, "
                       f"{len(entities.organizations)} orgs, "
                       f"{len(entities.topics)} topics")

            return entities

        except Exception as e:
            logger.error(f"Entity extraction failed: {str(e)}")
            # Return empty entities on failure
            return ExtractedEntities()

    def _build_system_prompt(self) -> str:
        """Build the system prompt for entity extraction."""
        return """You are an expert entity extraction system.
Your task is to extract relevant entities from the provided text.

Extract the following types of entities:
- people: Names of individuals, authors, experts, or roles
- organizations: Companies, institutions, agencies, or organizations
- locations: Places, cities, countries, regions, or addresses
- dates: Temporal references (dates, years, periods, time ranges)
- topics: Main subjects, themes, or key concepts
- technical_terms: Domain-specific terminology, acronyms, or specialized vocabulary

Guidelines:
1. Extract only entities explicitly mentioned in the text
2. Normalize entity names (e.g., "Dr. Smith" → "Dr. Smith", not variations)
3. Remove duplicates and near-duplicates
4. Focus on the most important and relevant entities
5. Keep entity names concise but complete
6. For topics, extract high-level themes, not every possible keyword"""

    def _build_user_prompt(self, text: str, context: Optional[str] = None) -> str:
        """Build the user prompt with the text to analyze."""
        prompt = f"Extract entities from the following text:\n\n{text}"

        if context:
            prompt = f"Document context: {context}\n\n" + prompt

        return prompt

    async def extract_entities_batch(
        self,
        texts: list[str],
        context: Optional[str] = None
    ) -> list[ExtractedEntities]:
        """
        Extract entities from multiple text chunks.

        Args:
            texts: List of text chunks
            context: Optional shared context

        Returns:
            List of ExtractedEntities, one per chunk
        """
        results = []
        for i, text in enumerate(texts):
            logger.debug(f"Extracting entities from chunk {i+1}/{len(texts)}")
            entities = await self.extract_entities(text, context)
            results.append(entities)

        return results

    def merge_entities(self, entity_list: list[ExtractedEntities]) -> ExtractedEntities:
        """
        Merge entities from multiple chunks, removing duplicates.

        Args:
            entity_list: List of ExtractedEntities to merge

        Returns:
            Single ExtractedEntities with unique entities
        """
        merged = ExtractedEntities()

        # Collect all entities
        all_people = set()
        all_orgs = set()
        all_locations = set()
        all_dates = set()
        all_topics = set()
        all_terms = set()

        for entities in entity_list:
            all_people.update(entities.people)
            all_orgs.update(entities.organizations)
            all_locations.update(entities.locations)
            all_dates.update(entities.dates)
            all_topics.update(entities.topics)
            all_terms.update(entities.technical_terms)

        # Assign to merged object
        merged.people = sorted(list(all_people))
        merged.organizations = sorted(list(all_orgs))
        merged.locations = sorted(list(all_locations))
        merged.dates = sorted(list(all_dates))
        merged.topics = sorted(list(all_topics))
        merged.technical_terms = sorted(list(all_terms))

        return merged
