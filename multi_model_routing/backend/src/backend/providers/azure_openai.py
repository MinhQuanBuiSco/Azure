"""Azure OpenAI provider via Microsoft Foundry."""

import logging
import time
import uuid
from typing import Any, AsyncIterator

from backend.config import Settings
from backend.models import Message
from backend.providers.base import BaseProvider

logger = logging.getLogger(__name__)


class AzureOpenAIProvider(BaseProvider):
    """Azure OpenAI API provider via Microsoft Foundry."""

    def __init__(self, settings: Settings) -> None:
        """Initialize the Azure OpenAI provider."""
        self._settings = settings
        self._client = None
        self._async_client = None

    def _get_async_client(self):
        """Get or create the async Azure OpenAI client."""
        if self._async_client is None:
            from openai import AsyncAzureOpenAI

            self._async_client = AsyncAzureOpenAI(
                azure_endpoint=self._settings.foundry_openai_endpoint,
                api_key=self._settings.foundry_api_key.get_secret_value(),
                api_version=self._settings.foundry_api_version,
            )
        return self._async_client

    def _convert_messages(self, messages: list[Message]) -> list[dict[str, Any]]:
        """Convert Message objects to Azure OpenAI format."""
        result = []
        for msg in messages:
            converted = {"role": msg.role}
            if msg.content is not None:
                converted["content"] = msg.content
            if msg.name:
                converted["name"] = msg.name
            if msg.tool_calls:
                converted["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                converted["tool_call_id"] = msg.tool_call_id
            result.append(converted)
        return result

    def _get_deployment_name(self, model: str) -> str:
        """Map model ID to deployment name. Model ID matches deployment name."""
        return model

    async def chat_completion(
        self,
        messages: list[Message],
        model: str,
        temperature: float = 1.0,
        max_tokens: int | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any] | AsyncIterator[dict[str, Any]]:
        """Send a chat completion request to Azure OpenAI."""
        client = self._get_async_client()
        deployment = self._get_deployment_name(model)

        # Build request parameters
        request_params: dict[str, Any] = {
            "model": deployment,
            "messages": self._convert_messages(messages),
            "temperature": temperature,
        }

        if max_tokens:
            request_params["max_tokens"] = max_tokens

        # Add optional parameters
        for key in ["top_p", "frequency_penalty", "presence_penalty", "stop"]:
            if key in kwargs:
                request_params[key] = kwargs[key]

        try:
            if stream:
                return self._stream_completion(client, request_params, model)
            else:
                response = await client.chat.completions.create(**request_params)
                return self._format_response(response, model)
        except Exception as e:
            logger.error(f"Azure OpenAI error: {e}")
            raise

    async def _stream_completion(
        self,
        client: Any,
        request_params: dict[str, Any],
        model: str,
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream chat completion response."""
        request_id = str(uuid.uuid4())
        created = int(time.time())

        stream = await client.chat.completions.create(**request_params, stream=True)
        async for chunk in stream:
            if chunk.choices:
                choice = chunk.choices[0]
                yield {
                    "id": request_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": model,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {
                                "role": getattr(choice.delta, "role", None),
                                "content": getattr(choice.delta, "content", None),
                            },
                            "finish_reason": choice.finish_reason,
                        }
                    ],
                }

    def _format_response(self, response: Any, model: str) -> dict[str, Any]:
        """Format Azure OpenAI response to standard format."""
        choices = []
        for choice in response.choices:
            choices.append(
                {
                    "index": choice.index,
                    "message": {
                        "role": choice.message.role,
                        "content": choice.message.content,
                    },
                    "finish_reason": choice.finish_reason,
                }
            )

        result: dict[str, Any] = {
            "id": response.id,
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": choices,
        }

        if response.usage:
            result["usage"] = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return result

    async def health_check(self) -> bool:
        """Check if Azure OpenAI is accessible."""
        try:
            client = self._get_async_client()
            response = await client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1,
            )
            return response is not None
        except Exception as e:
            logger.warning(f"Azure OpenAI health check failed: {e}")
            return False

    async def close(self) -> None:
        """Close the client connections."""
        if self._async_client:
            await self._async_client.close()
            self._async_client = None
