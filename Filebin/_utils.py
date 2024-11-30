from aiohttp import ClientSession, ClientTimeout, ClientResponse
from typing import AsyncGenerator, Any, Dict, Optional, Tuple, Union
from contextlib import asynccontextmanager
import gzip
import io
import json


@asynccontextmanager
async def _fetch(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Union[Dict[str, Any], str, bytes]] = None,
    json: Optional[Dict[str, Any]] = None,
    timeout: int = 10,
) -> AsyncGenerator[ClientResponse, None]:
    """
    Asynchronous context manager to perform an HTTP request.

    Args:
        url (str): The URL to send the request to.
        method (str): The HTTP method (e.g., GET, POST, PUT, DELETE). Default is "GET".
        headers (Optional[Dict[str, str]]): Optional headers for the request.
        params (Optional[Dict[str, Any]]): Optional query parameters for the request.
        data (Optional[Union[Dict[str, Any], str, bytes]]): Data to send in the request body.
        json (Optional[Dict[str, Any]]): JSON data to send in the request body.
        timeout (int): Timeout for the request in seconds. Default is 10.

    Yields:
        ClientResponse: The aiohttp response object.

    Raises:
        aiohttp.ClientError: If the request fails.
    """
    async with ClientSession() as session:
        try:
            async with session.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=params,
                data=data,
                json=json,
                timeout=ClientTimeout(total=timeout),
            ) as response:
                yield response
        except Exception as e:
            raise RuntimeError(f"HTTP request failed: {e}")
        

async def _response_parser(response: ClientResponse) -> Tuple[int, Any]:
        _content_type = response.headers.get("Content-Type", None)
        _content_encoding = response.headers.get("Content-Encoding", None)
        _r = [response.status, None]

        # decompression
        decompressed_content = None
        compressed_content = b''
        if 'gzip' in _content_encoding:
            # Decompress the response content using gzip
            # stream download
            while True:
                if _chunk := await response.content.readany():
                    compressed_content += _chunk
                else:
                    break
            try:
                compressed_file = io.BytesIO(compressed_content)
                with gzip.GzipFile(fileobj=compressed_file, mode='rb') as f:
                    decompressed_content = f.read().decode('utf-8')
            except gzip.BadGzipFile:
                # Content-Type header indicates gzip, but the content is not valid gzip
                decompressed_content = compressed_content.decode('utf-8')

        # --
        if "application/json" in _content_type:
            _r[1] = json.loads(decompressed_content) if decompressed_content else await response.json()
        elif "text/plain" in _content_type and _content_encoding:  # errors only
            _r[1] = decompressed_content if decompressed_content else await response.text()
        elif any(_e in _content_type for _e in ["image", "application", "text"]):
            _r[1] = b''
            while _chunk := await response.content.readany():
                _r[1] += _chunk
        else:
            _r[1] = response

        return tuple(_r)
