"""Azure Foundry provider for Claude models via Microsoft Foundry."""

import logging
import time
import uuid
from typing import Any, AsyncIterator

import httpx

from backend.config import Settings
from backend.models import Message
from backend.providers.base import BaseProvider

logger = logging.getLogger(__name__)


class AzureFoundryProvider(BaseProvider):
    """
    Azure Foundry provider for Claude models.

    Uses Microsoft Foundry's Anthropic-compatible API endpoint.
    Endpoint format: https://<resource>.services.ai.azure.com/anthropic/v1/messages
    """

    ANTHROPIC_VERSION = "2023-06-01"

    def __init__(self, settings: Settings) -> None:
        """Initialize the Azure Foundry provider."""
        self._settings = settings
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(300.0, connect=60.0),
            )
        return self._client

    def _get_base_url(self) -> str:
        """Get the Foundry Anthropic endpoint."""
        return self._settings.foundry_anthropic_endpoint

    def _get_headers(self) -> dict[str, str]:
        """Get request headers."""
        return {
            "Content-Type": "application/json",
            "x-api-key": self._settings.foundry_api_key.get_secret_value(),
            "anthropic-version": self.ANTHROPIC_VERSION,
        }

    def _convert_messages(
        self, messages: list[Message]
    ) -> tuple[str | None, list[dict[str, Any]]]:
        """
        Convert messages to Anthropic format.

        Returns:
            Tuple of (system_message, conversation_messages)
        """
        system_message = None
        conversation = []

        for msg in messages:
            if msg.role == "system":
                if isinstance(msg.content, str):
                    system_message = msg.content
                elif isinstance(msg.content, list):
                    texts = [
                        block.get("text", "")
                        for block in msg.content
                        if isinstance(block, dict) and block.get("type") == "text"
                    ]
                    system_message = " ".join(texts)
            else:
                role = msg.role
                if role == "tool":
                    role = "user"

                content = msg.content
                if content is None:
                    content = ""

                conversation.append({"role": role, "content": content})

        # Ensure alternating user/assistant messages
        if conversation and conversation[0]["role"] != "user":
            conversation.insert(0, {"role": "user", "content": "Please respond."})

        return system_message, conversation

    async def chat_completion(
        self,
        messages: list[Message],
        model: str,
        temperature: float = 1.0,
        max_tokens: int | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any] | AsyncIterator[dict[str, Any]]:
        """Send a chat completion request to Azure Foundry."""
        client = self._get_client()
        base_url = self._get_base_url()
        headers = self._get_headers()

        system_message, conversation = self._convert_messages(messages)

        # Build request body
        body: dict[str, Any] = {
            "model": model,
            "messages": conversation,
            "max_tokens": max_tokens or 4096,
        }

        if system_message:
            body["system"] = system_message

        if temperature != 1.0:
            body["temperature"] = temperature

        if "top_p" in kwargs:
            body["top_p"] = kwargs["top_p"]

        if "stop" in kwargs:
            stop = kwargs["stop"]
            body["stop_sequences"] = stop if isinstance(stop, list) else [stop]

        if stream:
            body["stream"] = True

        try:
            if stream:
                return self._stream_completion(client, base_url, headers, body, model)
            else:
                response = await client.post(
                    f"{base_url}/v1/messages",
                    headers=headers,
                    json=body,
                )
                response.raise_for_status()
                return self._format_response(response.json(), model)
        except httpx.HTTPStatusError as e:
            logger.error(f"Azure Foundry HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Azure Foundry error: {e}")
            raise

    async def _stream_completion(
        self,
        client: httpx.AsyncClient,
        base_url: str,
        headers: dict[str, str],
        body: dict[str, Any],
        model: str,
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream chat completion response."""
        request_id = str(uuid.uuid4())
        created = int(time.time())

        async with client.stream(
            "POST",
            f"{base_url}/v1/messages",
            headers=headers,
            json=body,
        ) as response:
            response.raise_for_status()

            async for line in response.aiter_lines():
                if not line:
                    continue

                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break

                    try:
                        import json
                        event = json.loads(data)

                        # Handle different event types
                        event_type = event.get("type", "")

                        if event_type == "content_block_delta":
                            delta = event.get("delta", {})
                            if delta.get("type") == "text_delta":
                                yield {
                                    "id": request_id,
                                    "object": "chat.completion.chunk",
                                    "created": created,
                                    "model": model,
                                    "choices": [
                                        {
                                            "index": 0,
                                            "delta": {"content": delta.get("text", "")},
                                            "finish_reason": None,
                                        }
                                    ],
                                }
                        elif event_type == "message_stop":
                            yield {
                                "id": request_id,
                                "object": "chat.completion.chunk",
                                "created": created,
                                "model": model,
                                "choices": [
                                    {
                                        "index": 0,
                                        "delta": {},
                                        "finish_reason": "stop",
                                    }
                                ],
                            }
                    except Exception as e:
                        logger.warning(f"Failed to parse stream event: {e}")
                        continue

    def _format_response(self, response: dict[str, Any], model: str) -> dict[str, Any]:
        """Format Anthropic response to OpenAI-compatible format."""
        content = ""
        for block in response.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")

        usage = response.get("usage", {})

        return {
            "id": response.get("id", str(uuid.uuid4())),
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content,
                    },
                    "finish_reason": response.get("stop_reason", "stop"),
                }
            ],
            "usage": {
                "prompt_tokens": usage.get("input_tokens", 0),
                "completion_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            },
        }

    async def health_check(self) -> bool:
        """Check if Azure Foundry is accessible."""
        try:
            client = self._get_client()
            base_url = self._get_base_url()
            headers = self._get_headers()

            response = await client.post(
                f"{base_url}/v1/messages",
                headers=headers,
                json={
                    "model": self._settings.claude_haiku_deployment,
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 1,
                },
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Azure Foundry health check failed: {e}")
            return False

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
