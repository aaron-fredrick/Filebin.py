from __future__ import annotations

from typing import Dict, Optional

from aiohttp import ClientSession

from ._constants import BASE_URL
from ._http import parseResponse
from ._models import Bin, File
from .errors import InvalidBin


class API:
    """
    Async client for the Filebin.net API.

    Usage — async context manager (recommended):
        async with API() as api:
            bin = await api.getBin("my-bin-id")

    Usage — manual lifecycle:
        api = API()
        await api.start()
        bin = await api.getBin("my-bin-id")
        await api.close()
    """

    _DEFAULT_HEADERS = {
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9",
        "Cookie": "verified=2024-05-24",
        "Host": "filebin.net",
        "Referer": "https://filebin.net/",
        "Accept": "*/*",
        "Connection": "keep-alive",
    }

    _DEFAULT_COOKIES = {"verified": "2024-05-24"}

    def __init__(self) -> None:
        self._bins: Dict[str, Bin] = {}
        self._session: Optional[ClientSession] = None

    @property
    def bins(self) -> Dict[str, Bin]:
        """Locally cached bins, keyed by bin ID."""
        return self._bins

    async def start(self) -> API:
        """Initialize the HTTP session. Call this if not using the context manager."""
        self._ensureSessionCreated()
        return self

    async def close(self) -> None:
        """Close the underlying HTTP session and release resources."""
        if self._session is not None:
            await self._session.close()
            self._session = None

    def _ensureSessionCreated(self) -> None:
        if self._session is None:
            self._session = ClientSession(
                base_url=BASE_URL,
                headers=self._DEFAULT_HEADERS,
                cookies=self._DEFAULT_COOKIES,
            )

    async def getBin(self, bin_id: str, from_cache: bool = False) -> Bin:
        """
        Retrieve a bin by its ID.

        Args:
            bin_id: The unique identifier of the bin.
            from_cache: If True, return the locally cached bin without a network call.

        Returns:
            The Bin instance.

        Raises:
            KeyError: If from_cache is True and the bin is not in the local cache.
            InvalidBin: If the bin ID does not exist on the server.
        """
        if from_cache:
            return self._bins[bin_id]

        async with self._session.get(
            url=bin_id, headers={"Accept": "application/json"}
        ) as response:
            status, data = await parseResponse(response)

        if status == 200:
            self._bins[bin_id] = Bin(data=data, session=self._session)
        elif status == 404:
            raise InvalidBin(bin_id)

        return self._bins[bin_id]

    async def lockBin(self, bin_id: str) -> Bin:
        """
        Lock a bin, making it read-only.

        Args:
            bin_id: The ID of the bin to lock.

        Returns:
            The locked Bin instance.
        """
        bin = await self.getBin(bin_id)
        return await bin.lock()

    async def deleteBin(self, bin_id: str) -> bool:
        """
        Delete a bin and evict it from the local cache.

        Args:
            bin_id: The ID of the bin to delete.

        Returns:
            True if the bin was deleted successfully.
        """
        bin = await self.getBin(bin_id)
        deleted = await bin.delete()
        if deleted:
            self._bins.pop(bin_id, None)
        return deleted

    async def downloadArchivedBin(
        self, bin_id: str, archive_type: str, path: str = "."
    ) -> bool:
        """
        Download an entire bin as a zip or tar archive.

        Args:
            bin_id: The ID of the bin.
            archive_type: 'zip' or 'tar'.
            path: Local directory to save the archive. Defaults to CWD.

        Returns:
            True if the archive was written successfully.
        """
        bin = await self.getBin(bin_id)
        return await bin.downloadArchive(archive_type, path)

    async def getFile(
        self, bin_id: str, file_name: str, from_cache: bool = False
    ) -> File:
        """
        Retrieve a file from a specific bin by name.

        Args:
            bin_id: The bin containing the file.
            file_name: The name of the file to retrieve.
            from_cache: If True, search locally cached data only.

        Returns:
            The File instance.

        Raises:
            InvalidBin: If the bin is not found.
            InvalidFile: If the file is not found in the bin.
        """
        if from_cache and bin_id in self._bins:
            return await self._bins[bin_id].getFile(file_name, from_cache=True)

        bin = await self.getBin(bin_id)
        return await bin.getFile(file_name, from_cache=from_cache)

    async def __aenter__(self) -> API:
        self._ensureSessionCreated()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
