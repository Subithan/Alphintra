"""HTTP client helpers."""

from __future__ import annotations

import asyncio
from typing import Optional

import httpx

_client: Optional[httpx.AsyncClient] = None
_client_lock: Optional[asyncio.Lock] = None


async def get_http_client() -> httpx.AsyncClient:
    """Return shared async HTTP client instance."""

    global _client_lock, _client
    if _client is not None:
        return _client

    if _client_lock is None:
        _client_lock = asyncio.Lock()

    async with _client_lock:
        if _client is None:
            _client = httpx.AsyncClient(timeout=30.0)
    return _client


async def close_http_client() -> None:
    """Dispose the shared HTTP client."""

    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
