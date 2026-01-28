"""HTTP client service for external API calls."""

from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger()


class HTTPClient:
    """Async HTTP client with retry logic."""

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(20.0),
                follow_redirects=True,
            )
        return self._client

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
    )
    async def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Make GET request with retry logic."""
        client = await self._get_client()
        logger.debug("HTTP GET", url=url, params=params)

        response = await client.get(url, params=params, headers=headers)
        response.raise_for_status()

        return response.json()

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
    )
    async def post(
        self,
        url: str,
        data: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Make POST request with retry logic."""
        client = await self._get_client()
        logger.debug("HTTP POST", url=url)

        response = await client.post(
            url, data=data, json=json_data, headers=headers
        )
        response.raise_for_status()

        return response.json()

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


_http_client: HTTPClient | None = None


def get_http_client() -> HTTPClient:
    """Get or create HTTP client instance."""
    global _http_client
    if _http_client is None:
        _http_client = HTTPClient()
    return _http_client
