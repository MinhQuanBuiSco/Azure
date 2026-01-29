"""Anthropic provider."""

import logging
import time
import uuid
from typing import Any, AsyncIterator

from backend.config import Settings
from backend.models import Message
from backend.providers.base import BaseProvider

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseProvider):
    """Anthropic API provider."""

    def __init__(self, settings: Settings) -> None:
        """Initialize the Anthropic provider."""
        self._settings = settings
        self._client = None

    def _get_client(self):
        """Get or create the Anthropic client."""
        if self._client is None:
            import anthropic

            self._client = anthropic.AsyncAnthropic(
                api_key=self._settings.anthropic_api_key.get_secret_value()
            )
        return self._client

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
                # Anthropic uses a separate system parameter
                if isinstance(msg.content, str):
                    system_message = msg.content
                elif isinstance(msg.content, list):
                    # Extract text from content blocks
                    texts = [
                        block.get("text", "")
                        for block in msg.content
                        if isinstance(block, dict) and block.get("type") == "text"
                    ]
                    system_message = " ".join(texts)
            else:
                role = msg.role
                if role == "tool":
                    role = "user"  # Anthropic uses user for tool results

                content = msg.content
                if content is None:
                    content = ""

                conversation.append({"role": role, "content": content})

        # Ensure alternating user/assistant messages for Anthropic
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
        """Send a chat completion request to Anthropic."""
        client = self._get_client()

        system_message, conversation = self._convert_messages(messages)

        # Build request parameters
        request_params: dict[str, Any] = {
            "model": model,
            "messages": conversation,
            "max_tokens": max_tokens or 4096,
        }

        if system_message:
            request_params["system"] = system_message

        if temperature != 1.0:
            request_params["temperature"] = temperature

        # Add optional parameters
        if "top_p" in kwargs:
            request_params["top_p"] = kwargs["top_p"]
        if "stop" in kwargs:
            request_params["stop_sequences"] = (
                kwargs["stop"] if isinstance(kwargs["stop"], list) else [kwargs["stop"]]
            )

        try:
            if stream:
                return self._stream_completion(client, request_params, model)
            else:
                response = await client.messages.create(**request_params)
                return self._format_response(response, model)
        except Exception as e:
            logger.error(f"Anthropic error: {e}")
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

        async with client.messages.stream(**request_params) as stream:
            async for text in stream.text_stream:
                yield {
                    "id": request_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": model,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {
                                "content": text,
                            },
                            "finish_reason": None,
                        }
                    ],
                }

            # Final chunk with finish reason
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

    def _format_response(self, response: Any, model: str) -> dict[str, Any]:
        """Format Anthropic response to OpenAI-compatible format."""
        # Extract text content
        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text

        result: dict[str, Any] = {
            "id": response.id,
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
                    "finish_reason": response.stop_reason or "stop",
                }
            ],
        }

        if response.usage:
            result["usage"] = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            }

        return result

    async def health_check(self) -> bool:
        """Check if Anthropic is accessible."""
        try:
            client = self._get_client()
            response = await client.messages.create(
                model="claude-3-5-haiku-latest",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1,
            )
            return response is not None
        except Exception as e:
            logger.warning(f"Anthropic health check failed: {e}")
            return False

    async def close(self) -> None:
        """Close the client connection."""
        if self._client:
            await self._client.close()
            self._client = None
