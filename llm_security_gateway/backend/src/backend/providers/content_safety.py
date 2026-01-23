"""Azure AI Content Safety client."""

from typing import Any

from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import (
    AnalyzeTextOptions,
    TextCategory,
)
from azure.core.credentials import AzureKeyCredential

from backend.config.settings import get_settings
from backend.models.security import ContentSafetyResult


class AzureContentSafetyClient:
    """Client for Azure AI Content Safety API."""

    def __init__(self):
        self.settings = get_settings()
        self._client: ContentSafetyClient | None = None
        self._enabled = bool(
            self.settings.azure_content_safety_endpoint
            and self.settings.azure_content_safety_key
        )

    @property
    def enabled(self) -> bool:
        """Check if Content Safety is configured and enabled."""
        return self._enabled

    @property
    def client(self) -> ContentSafetyClient:
        """Lazy initialization of the client."""
        if self._client is None:
            if not self._enabled:
                raise ValueError(
                    "Azure Content Safety is not configured. "
                    "Set AZURE_CONTENT_SAFETY_ENDPOINT and AZURE_CONTENT_SAFETY_KEY."
                )
            self._client = ContentSafetyClient(
                endpoint=self.settings.azure_content_safety_endpoint,
                credential=AzureKeyCredential(self.settings.azure_content_safety_key),
            )
        return self._client

    async def analyze_text(
        self,
        text: str,
        categories: list[str] | None = None,
        block_threshold: int = 2,
    ) -> list[ContentSafetyResult]:
        """
        Analyze text for content safety violations.

        Args:
            text: The text to analyze
            categories: Categories to check (default: all)
            block_threshold: Severity level at which to block (0-6, default 2)

        Returns:
            List of ContentSafetyResult for each category
        """
        if not self._enabled:
            return []

        # Default categories
        if categories is None:
            categories = ["Hate", "Violence", "Sexual", "SelfHarm"]

        try:
            request = AnalyzeTextOptions(text=text)
            response = self.client.analyze_text(request)

            results = []

            # New SDK uses categories_analysis list
            if hasattr(response, 'categories_analysis') and response.categories_analysis:
                for category_result in response.categories_analysis:
                    results.append(
                        ContentSafetyResult(
                            category=str(category_result.category).replace("TextCategory.", ""),
                            severity=category_result.severity,
                            blocked=category_result.severity >= block_threshold,
                        )
                    )
            else:
                # Fallback for older SDK format
                if hasattr(response, 'hate_result') and response.hate_result:
                    results.append(
                        ContentSafetyResult(
                            category="Hate",
                            severity=response.hate_result.severity,
                            blocked=response.hate_result.severity >= block_threshold,
                        )
                    )
                if hasattr(response, 'violence_result') and response.violence_result:
                    results.append(
                        ContentSafetyResult(
                            category="Violence",
                            severity=response.violence_result.severity,
                            blocked=response.violence_result.severity >= block_threshold,
                        )
                    )
                if hasattr(response, 'sexual_result') and response.sexual_result:
                    results.append(
                        ContentSafetyResult(
                            category="Sexual",
                            severity=response.sexual_result.severity,
                            blocked=response.sexual_result.severity >= block_threshold,
                        )
                    )
                if hasattr(response, 'self_harm_result') and response.self_harm_result:
                    results.append(
                        ContentSafetyResult(
                            category="SelfHarm",
                            severity=response.self_harm_result.severity,
                            blocked=response.self_harm_result.severity >= block_threshold,
                        )
                    )

            return results

        except Exception as e:
            print(f"Content Safety API error: {e}")
            return []

    async def check_prompt_shield(self, user_prompt: str, documents: list[str] | None = None) -> dict[str, Any]:
        """
        Check for prompt injection attacks using Prompt Shields.

        Note: This is a placeholder for the Prompt Shields API which may require
        additional setup in Azure AI Content Safety.

        Args:
            user_prompt: The user's prompt to check
            documents: Optional list of documents/context

        Returns:
            Dict with attack detection results
        """
        if not self._enabled:
            return {"detected": False, "reason": "Content Safety not configured"}

        # Prompt Shields would be called here when available
        # For now, return a placeholder
        return {
            "detected": False,
            "user_prompt_attack": False,
            "document_attack": False,
        }

    def close(self):
        """Close the client connection."""
        if self._client:
            self._client.close()
            self._client = None


# Global client instance
_client: AzureContentSafetyClient | None = None


def get_content_safety_client() -> AzureContentSafetyClient:
    """Get or create the Content Safety client."""
    global _client
    if _client is None:
        _client = AzureContentSafetyClient()
    return _client
