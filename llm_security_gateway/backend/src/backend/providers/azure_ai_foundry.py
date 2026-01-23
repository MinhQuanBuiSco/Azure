"""Azure AI Foundry client for LLM inference."""

import time
from typing import Any, AsyncIterator

import httpx
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import (
    ChatCompletions,
    ChatRequestMessage,
    SystemMessage,
    UserMessage,
    AssistantMessage,
)
from azure.core.credentials import AzureKeyCredential

from backend.config.settings import get_settings
from backend.models.requests import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    ChatMessage,
    Usage,
)


class AzureAIFoundryClient:
    """Client for Azure AI Foundry inference API."""

    def __init__(self):
        self.settings = get_settings()
        self._client: ChatCompletionsClient | None = None

    @property
    def client(self) -> ChatCompletionsClient:
        """Lazy initialization of the client."""
        if self._client is None:
            if not self.settings.azure_ai_endpoint or not self.settings.azure_ai_api_key:
                raise ValueError(
                    "Azure AI Foundry endpoint and API key must be configured. "
                    "Set AZURE_AI_ENDPOINT and AZURE_AI_API_KEY environment variables."
                )
            # For Azure OpenAI, construct the full endpoint with deployment name
            base_endpoint = self.settings.azure_ai_endpoint.rstrip("/")
            deployment_name = self.settings.azure_ai_deployment_name

            # Azure AI Inference SDK expects endpoint format:
            # https://<resource>.openai.azure.com/openai/deployments/<deployment>
            if "openai.azure.com" in base_endpoint and "/openai/deployments/" not in base_endpoint:
                endpoint = f"{base_endpoint}/openai/deployments/{deployment_name}"
            else:
                endpoint = base_endpoint

            self._client = ChatCompletionsClient(
                endpoint=endpoint,
                credential=AzureKeyCredential(self.settings.azure_ai_api_key),
            )
        return self._client

    def _convert_messages(self, messages: list[ChatMessage]) -> list[ChatRequestMessage]:
        """Convert OpenAI-style messages to Azure AI Foundry format."""
        converted = []
        for msg in messages:
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            if msg.role == "system":
                converted.append(SystemMessage(content=content))
            elif msg.role == "user":
                converted.append(UserMessage(content=content))
            elif msg.role == "assistant":
                converted.append(AssistantMessage(content=content))
            else:
                # Default to user message for unknown roles
                converted.append(UserMessage(content=content))
        return converted

    async def chat_completion(
        self, request: ChatCompletionRequest
    ) -> ChatCompletionResponse:
        """
        Send a chat completion request to Azure AI Foundry.

        Args:
            request: The chat completion request

        Returns:
            ChatCompletionResponse with the model's response
        """
        messages = self._convert_messages(request.messages)

        # Build request parameters
        params: dict[str, Any] = {
            "messages": messages,
            "model": request.model or self.settings.azure_ai_deployment_name,
        }

        if request.temperature is not None:
            params["temperature"] = request.temperature
        if request.top_p is not None:
            params["top_p"] = request.top_p
        if request.max_tokens is not None:
            params["max_tokens"] = request.max_tokens
        if request.stop is not None:
            params["stop"] = request.stop
        if request.presence_penalty is not None:
            params["presence_penalty"] = request.presence_penalty
        if request.frequency_penalty is not None:
            params["frequency_penalty"] = request.frequency_penalty

        # Make the API call
        response: ChatCompletions = self.client.complete(**params)

        # Convert response to OpenAI format
        choices = []
        for i, choice in enumerate(response.choices):
            choices.append(
                ChatCompletionChoice(
                    index=i,
                    message=ChatMessage(
                        role=choice.message.role,
                        content=choice.message.content,
                    ),
                    finish_reason=choice.finish_reason,
                )
            )

        return ChatCompletionResponse(
            id=response.id,
            object="chat.completion",
            created=int(time.time()),
            model=response.model or request.model,
            choices=choices,
            usage=Usage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            ) if response.usage else None,
        )

    async def chat_completion_stream(
        self, request: ChatCompletionRequest
    ) -> AsyncIterator[str]:
        """
        Stream a chat completion request.

        Args:
            request: The chat completion request

        Yields:
            Server-sent event strings
        """
        messages = self._convert_messages(request.messages)

        params: dict[str, Any] = {
            "messages": messages,
            "model": request.model or self.settings.azure_ai_deployment_name,
            "stream": True,
        }

        if request.temperature is not None:
            params["temperature"] = request.temperature
        if request.top_p is not None:
            params["top_p"] = request.top_p
        if request.max_tokens is not None:
            params["max_tokens"] = request.max_tokens

        # Note: Streaming implementation would use the streaming API
        # For now, fall back to non-streaming
        response = await self.chat_completion(request)
        yield f"data: {response.model_dump_json()}\n\n"
        yield "data: [DONE]\n\n"

    def close(self):
        """Close the client connection."""
        if self._client:
            self._client.close()
            self._client = None


# Global client instance
_client: AzureAIFoundryClient | None = None


def get_azure_ai_client() -> AzureAIFoundryClient:
    """Get or create the Azure AI Foundry client."""
    global _client
    if _client is None:
        _client = AzureAIFoundryClient()
    return _client
