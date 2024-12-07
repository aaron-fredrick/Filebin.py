from __future__ import annotations

from aiohttp import ClientSession, ClientTimeout, ClientResponse

from .Errors import *
from typing import TYPE_CHECKING, Tuple, Union, Optional, List, Any, Self

from ._constants import BASE_URL
from ._utils import _fetch, _response_parser
from ._classes import _BIN, _FILE

if TYPE_CHECKING:
    from Filebin import API  # Import self for type checking


class API:
    def __init__(self):
        self.__bins = {}
        self.__session = None
        
    
    @property
    def bins(self) -> dict[str, _BIN]:
        return self.__bins

    async def __createSessionIfNotExist(self) -> None:
        if self.__session is None:
            self.__session = ClientSession(
                base_url="https://filebin.net",
                headers={
                    "Accept-Encoding": "gzip, deflate, br, zstd",
                    "Accept-Language": "en-US,en;q=0.9,en-GB;q=0.8",
                    "Cookie": "verified=2024-05-24",
                    "Host": "filebin.net",
                    "Referer": "https://filebin.net/",
                    "accept": "*/*",
                    "Connection": "keep-alive"
                },
                cookies={
                    "verified": "2024-05-24"
                }
            )

    # API public methods
    # BIN functions
    async def getBin(self, _id: str, _from_cache: bool = False) -> Optional[_BIN]:
        """
        Retrieve a bin from Filebin by its unique identifier.

        Args:
            _id (str): The unique identifier of the bin to retrieve.
            _from_cache (bool, optional): If True, fetch the bin from the local cache
                instead of making an API call. Defaults to False.

        Returns:
            Optional[_BIN]: An instance of the `_BIN` class if the bin is found,
            either from the cache or the API. Returns None if the bin is not found
            and `_from_cache` is True.

        Raises:
            InvalidBin: If the bin ID is not found on the server.
        """

        if _from_cache:
            return self.bins.get(_id, None)
        else:
            async with self.__session.get(
                url=_id,
                headers={"Accept": "application/json"}
            ) as response:
                _r = await _response_parser(response=response)
                if _r[0] == 200:
                    self.__bins[_id] = _BIN(_r[1], self.__session)
                elif _r[0] == 404:
                    raise InvalidBin(_id)

            return self.__bins[_id]
        
    async def lockBin(self, _id: str) -> _BIN:
        if bin:=await self.getBin(_id):
            return await bin.lock()
        
    async def deleteBin(self, _id: str) -> bool:
        if bin:=await self.getBin(_id):
            return await bin.delete()

    async def downloadArchivedBin(self, _id: str, _type: str, _path: str = ".") -> bool:
        if bin:=await self.getBin(_id):
            return await bin.downloadArchive(_type, _path)

    # FILE functions
    async def getFile(self, _bin_id: str, _file_name: str, _from_cache: bool = False) -> Optional[_FILE]:
        """
        Retrieve a file from a specific bin in Filebin.

        Args:
            _bin_id (str): The unique identifier of the bin containing the file.
            _file_name (str): The name of the file to retrieve.
            _from_cache (bool, optional): If True, fetch the file from the local
                cache instead of making an API call. Defaults to False.

        Returns:
            Optional[_FILE]: An instance of the `_FILE` class if the file is found,
            either from the cache or the API. Returns None if the bin or file is not
            found and `_from_cache` is True.

        Raises:
            InvalidBin: If the bin ID is not found on the server.
            InvalidFile: If the file name is not found in the bin.
        """

        # Fetch bin from cache if available
        bin = self.bins.get(_bin_id, None)

        # If using cache, return the file directly if the bin exists
        if _from_cache and  bin is not None:
            return await bin.getFile(_file_name, _from_cache)
        elif _from_cache:
            return None  # If bin is not in cache, return None

        # If not using cache, fetch the bin if it's not already cached
        if bin is None:
            bin = await self.getBin(_bin_id)

        # Fetch the file from the bin
        return await bin.getFile(_file_name, _from_cache)

    async def __aenter__(self):
        """
        Prepare the API instance for use in an asynchronous context.
        This method can be used to initialize resources like session objects.
        """
        # Initialize resources if necessary (e.g., HTTP session)

        await self.__createSessionIfNotExist()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Clean up resources when the API instance is used in an asynchronous context.
        This method ensures any resources are properly closed.
        """
        await self.__session.close()
        pass