from __future__ import annotations

import gzip
import io
import json as _json

from aiohttp import ClientResponse
from typing import Any, Tuple


async def parseResponse(response: ClientResponse) -> Tuple[int, Any]:
    """
    Parse an aiohttp response into a (status_code, body) tuple.

    The body is decoded as JSON, plain text, or raw bytes depending on
    the Content-Type header. Gzip-compressed responses are decompressed
    transparently before parsing.

    Args:
        response: The aiohttp ClientResponse to parse.

    Returns:
        A tuple of (HTTP status code, parsed response body).
    """
    content_type = response.headers.get("Content-Type", "")
    content_encoding = response.headers.get("Content-Encoding", "")

    raw_body = await _readBody(response, content_encoding)

    parsed_body = _decodeBody(raw_body, content_type, content_encoding, response)
    return response.status, parsed_body


async def _readBody(response: ClientResponse, content_encoding: str) -> bytes:
    """Read the full response body, decompressing gzip if required."""
    compressed = b""
    async for chunk in response.content.iter_any():
        compressed += chunk

    if "gzip" in content_encoding:
        return _decompressGzip(compressed)

    return compressed


def _decompressGzip(data: bytes) -> bytes:
    """Decompress gzip-encoded bytes, falling back to raw bytes on failure."""
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(data), mode="rb") as gz:
            return gz.read()
    except gzip.BadGzipFile:
        return data


def _decodeBody(
    raw: bytes,
    content_type: str,
    content_encoding: str,
    response: ClientResponse,
) -> Any:
    """Decode raw response bytes according to the Content-Type header."""
    if "application/json" in content_type:
        return _json.loads(raw.decode("utf-8"))

    if "text/plain" in content_type and content_encoding:
        return raw.decode("utf-8")

    if any(kind in content_type for kind in ("image/", "application/", "text/")):
        return raw

    return response
