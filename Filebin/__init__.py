from __future__ import annotations

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

    @property
    def bins(self) -> dict[str, _BIN]:
        return self.__bins

    # API public methods
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
            async with _fetch(
                url=f"{BASE_URL}/{_id}",
                method="GET",
                headers={"Accept": "application/json"}
            ) as response:
                _r = await _response_parser(response=response)
                if _r[0] == 200:
                    self.__bins[_id] = _BIN(_r[1])
                elif _r[0] == 404:
                    raise InvalidBin(_id)

            return self.__bins[_id]

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
        bin = self.bins.get(_bin_id)

        # If using cache, return the file directly if the bin exists
        if _from_cache:
            if bin is not None:
                return await bin.getFile(_file_name, _from_cache)
            return None  # If bin is not in cache, return None

        # If not using cache, fetch the bin if it's not already cached
        if bin is None:
            bin = await self.getBin(_bin_id)

        # Fetch the file from the bin
        return await bin.getFile(_file_name, _from_cache)
