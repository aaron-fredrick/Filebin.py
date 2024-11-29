from __future__ import annotations

import aiohttp
from aiohttp import ClientResponse
import datetime as dt
from datetime import datetime
from Filebin.Errors import *
import gzip
import io
from io import BytesIO
import json
import numpy as np
from PIL import Image
from typing import TYPE_CHECKING, Tuple, Union, Optional, List, Any, Self

if TYPE_CHECKING:
    from Filebin import API  # Import self for type checking

BASE_URL = "https://filebin.net"


class API:
    def __init__(self):
        self.__base_endpoint = BASE_URL
        self.__bins = {}

    # Bin
    class _BIN:
        def __init__(BIN, _r: dict, _get, _post, _put, _delete):
            # fetching functions
            BIN.__get = _get
            BIN.__post = _post
            BIN.__put = _put
            BIN.__delete = _delete

            # setting up properties
            BIN.__setProperties(_r=_r)

            BIN.__qr = None

            BIN.__locally_updated_at = datetime.now()

        class _FILE:
            def __init__(FILE, _f: dict, _bin: API._BIN, _get, _delete):
                # BIN info
                FILE.__bin = _bin

                # fetching functions
                FILE.__get = _get
                FILE.__delete = _delete

                # file properties
                FILE.__name = _f.get("filename", None)
                FILE.__content_type = _f.get("content-type", None)
                FILE.__bytes = _f.get("bytes", None)
                FILE.__md5 = _f.get("md5", None)
                FILE.__sha256 = _f.get("sha256", None)
                FILE.__updated_at = datetime.strptime(
                    _dt, "%Y-%m-%dT%H:%M:%S.%fZ") if (_dt := _f.get("updated_at", None)) is not None else None
                FILE.__created_at = datetime.strptime(
                    _dt, "%Y-%m-%dT%H:%M:%S.%fZ") if (_dt := _f.get("created_at", None)) is not None else None

                FILE.__locally_updated_at = datetime.now()

            # properties
            @property
            def bin(FILE) -> API._BIN:
                return FILE.__bin

            @property
            def name(FILE) -> Optional[str]:
                return FILE.__name

            @property
            def content_type(FILE) -> bool | None:
                return FILE.__content_type

            @property
            def bytes(FILE) -> int | None:
                return FILE.__bytes

            @property
            def md5(FILE) -> int | None:
                return FILE.__md5

            @property
            def sha256(FILE) -> int | None:
                return FILE.__sha256

            @property
            def updated_at(FILE) -> Optional[datetime]:
                return FILE.__updated_at

            @property
            def created_at(FILE) -> Optional[datetime]:
                return FILE.__created_at

            @property
            def locally_updated_at(FILE) -> datetime:
                return FILE.__locally_updated_at

            # FILE methods
            async def download(FILE, _path: str = ".") -> bool:
                return await FILE.bin.downloadFile(FILE.name, _path)

            async def delete(FILE) -> bool:
                return await FILE.__delete(f"{FILE.bin.id}/{FILE.name}")

        class _QR:
            def __init__(QR, _image_bytes: bytes, _bin_id: str):
                QR.__image_bytes = _image_bytes
                n = _bin_id

            @property
            def image_bytes(QR) -> bytes:
                return QR.__image_bytes

            # methods of QR
            def show(QR) -> None:
                try:
                    Image.fromarray((np.array(Image.open(BytesIO(QR.__image_bytes))) * 255).astype('uint8')).show(
                        "bin qr")
                except Exception as e:
                    print(f"Error opening image: {e}")

            def save(QR, _path: str = "."):
                try:
                    Image.fromarray((np.array(Image.open(BytesIO(QR.__image_bytes))) * 255).astype('uint8')).save(
                        f"{_path}/{n}.png")
                except Exception as e:
                    print(f"Error opening image: {e}")

            def __str__(QR):
                image = Image.open(BytesIO(QR.__image_bytes))

                # Resize the image to fit the console width
                console_width = 40
                aspect_ratio = image.width / image.height
                new_width = int(console_width * 0.8)
                new_height = int(new_width / aspect_ratio)
                resized_image = image.resize((new_width, new_height))

                # Convert the image to ANSI escape code sequences
                ansi_image = ""
                for y in range(resized_image.height):
                    for x in range(resized_image.width):
                        pixel = resized_image.getpixel((x, y))
                        pixel_color = f"\x1b[48;2;{
                            abs(pixel - 1) * 255};{abs(pixel - 1) * 255};{abs(pixel - 1) * 255}m"
                        ansi_image += f"{pixel_color} " * 2
                    # Reset color at the end of each line
                    ansi_image += "\x1b[0m\n"

                return ansi_image

        # BIN property/attr private setter
        def __setProperties(BIN, _r: dict) -> None:
            r_bin = _r.get("bin", {})

            # bin properties
            BIN.__id = r_bin.get("id", None)
            BIN.__readonly = r_bin.get("readonly", None)
            BIN.__bytes = r_bin.get("bytes", None)

            # bin date time based properties
            for key in ["updated_at", "created_at", "expired_at"]:
                setattr(BIN, f"__{key}", datetime.strptime(
                    _dt, "%Y-%m-%dT%H:%M:%S.%fZ") if (_dt := r_bin.get(key, None)) is not None else None)

                print(getattr(BIN, f"__{key}"))

            BIN.__updated_at = datetime.strptime(_dt, "%Y-%m-%dT%H:%M:%S.%fZ") if (
                _dt := r_bin.get("updated_at", None)) is not None else None
            BIN.__created_at = datetime.strptime(_dt, "%Y-%m-%dT%H:%M:%S.%fZ") if (
                _dt := r_bin.get("created_at", None)) is not None else None
            BIN.__expired_at = datetime.strptime(_dt, "%Y-%m-%dT%H:%M:%S.%fZ") if (
                _dt := r_bin.get("expired_at", None)) is not None else None

            # files
            BIN.__files = [BIN._FILE(
                _f=_f, _bin=BIN, _get=BIN.__get, _delete=BIN.__delete) for _f in _r.get("files", [])]

        # BIN property/attr accessors
        @property
        def id(BIN) -> Optional[str]:
            return BIN.__id

        @property
        def readonly(BIN) -> Optional[bool]:
            return BIN.__readonly

        @property
        def bytes(BIN) -> Optional[int]:
            return BIN.__bytes

        @property
        def files(BIN) -> List[_FILE]:
            return BIN.__files

        @property
        def updated_at(BIN) -> Optional[datetime]:
            return BIN.__updated_at

        @property
        def created_at(BIN) -> Optional[datetime]:
            return BIN.__created_at

        @property
        def expired_at(BIN) -> Optional[datetime]:
            return BIN.__expired_at

        @property
        def locally_updated_at(BIN) -> datetime:
            return BIN.__locally_updated_at

        @property
        async def qr(BIN) -> _QR:
            qr = None
            if BIN.__qr:
                qr = BIN.__qr
            else:
                _r = await BIN.__get(f"qr/{BIN.id}", {"Accept": "image/png"})
                if _r[0] == 200:
                    qr = BIN._QR(_image_bytes=_r[1], _bin_id=BIN.id)
                elif _r[0] == 404:
                    raise InvalidBin(BIN.id)

            return qr

        # BIN methods
        async def update(BIN) -> object:
            _, _r = await BIN.__get(_url=BIN.id, _headers={"Accept": "application/json"})

            BIN.__setProperties(_r)
            
            BIN.__locally_updated_at = datetime.now()

            # returning self
            return BIN

        async def lock(BIN) -> object:
            await BIN.__put(BIN.id, {"Accept": "application/json"})

            await BIN.update()

            if BIN.readonly:
                try:
                    delattr(BIN, "uploadFile")
                except AttributeError:
                    print("--x--")

            return BIN  # return self

        async def delete(BIN) -> bool:
            return await BIN.__delete(BIN.id)

        async def downloadArchive(BIN, _type: str, _path: str = ".") -> bool:
            return_bool = False
            if _type in ["tar", "zip"]:
                _r = await BIN.__get(f"archive/{BIN.id}/{_type}")

                if _r[0] == 200:
                    with open(f"{_path}/{BIN.id}.{_type}", "wb") as f:
                        f.write(_r[1])
                        return_bool = True
                elif _r[0] == 404:
                    raise InvalidBin(BIN.id)

                else:
                    raise InvalidArchiveType(_type)

            return return_bool

        async def getFile(BIN, _file_name: str, _from_cache: bool = False) -> Optional[_FILE]:
            return_file = None

            def _rf(_fn: str):
                for _f in BIN.files:
                    if _f.name == _file_name:
                        return _f

            if _from_cache:
                return_file = _rf(_fn=_file_name)
            else:
                await BIN.update()
                return_file = _rf(_fn=_file_name)

            return return_file

        async def downloadFile(BIN, _file_name: str, _path: str = ".") -> bool:
            return_bool = False

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{BASE_URL}/{BIN.id}/{_file_name}",
                    headers={
                        "Accept-Encoding": "gzip, deflate, br, zstd",
                        "Accept-Language": "en-US,en;q=0.9,en-GB;q=0.8",
                        "Cookie": "verified=2024-05-24",
                        "Host": "filebin.net",
                        "Referer": "https://filebin.net/",
                        "accept": "*/*",
                    },
                        allow_redirects=False
                ) as response_1:
                    if response_1.status in (301, 302):
                        if (s3_location := response_1.headers.get("Location")):
                            async with session.get(
                                s3_location,
                                headers={
                                    "Host": "s3.filebin.net",
                                    "Referer": "https://filebin.net/",
                                    "accept": "*/*",
                                },
                                allow_redirects=False
                            ) as response_2:
                                if response_2.status == 200:
                                    with open(f"{_path}/{_file_name}", "wb") as f:
                                        while chunk := await response_2.content.readany():
                                            f.write(chunk)
                                    return_bool = True

                    elif response_1.status == 403:
                        raise DownloadCountReached(_file_name)
                    elif response_1.status == 404:
                        raise InvalidFile(_file_name)

            return return_bool

        async def deleteFile(BIN, _file_name: str) -> bool:
            return_bool = False

            _r = await BIN.__delete(f"{BIN.id}/{_file_name}", {"Accept": "application/json"})

            if _r[0] == 200:
                return_bool = True
            elif _r[0] == 404:
                raise InvalidBinOrFile(_bin_id=BIN.id, _file_name=_file_name)

            return return_bool

        async def uploadFile(BIN, _file: str) -> bool:
            ...

        def __hash__(BIN) -> str:
            return BIN.id

        def __str__(BIN) -> str:
            return ""

            # properties

    @property
    def bins(self) -> dict:
        return self.__bins

    async def __response_parser(self, response: ClientResponse) -> Tuple[int, Union[None, dict, str, bytes, ClientResponse, Any, ...]]:
        _content_type = response.headers.get("Content-Type", None)
        _content_encoding = response.headers.get("Content-Encoding", None)
        # print(dict(response.headers))
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
            while True:
                _chunk = await response.content.readany()
                if not _chunk:
                    break
                _r[1] += _chunk
        else:
            _r[1] = response

        return tuple(_r)

    # methods
    async def __get(self, _url: str, _headers: dict = {"Accept": "*/*"}) -> Tuple[int, Union[None, dict, str, bytes]]:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.__base_endpoint}/{_url}", headers=_headers) as response:
                return await self.__response_parser(response=response)

    async def __post(self, _url: str, _body, _headers: dict | None = None) -> Tuple[int, Union[None, dict, str, bytes]]:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.__base_endpoint}/{_url}", headers=_headers) as response:
                return await self.__response_parser(response=response)

    async def __put(self, _url: str, _headers: dict | None = None) -> Tuple[int, Union[None, dict, str, bytes]]:
        async with aiohttp.ClientSession() as session:
            async with session.put(f"{self.__base_endpoint}/{_url}", headers=_headers) as response:
                return await self.__response_parser(response=response)

    async def __delete(self, _url: str, _headers: dict | None = None) -> Tuple[int, Union[None, dict, str, bytes]]:
        async with aiohttp.ClientSession() as session:
            async with session.delete(f"{self.__base_endpoint}/{_url}", headers=_headers) as response:
                return await self.__response_parser(response=response)

    # API public methods
    async def getBin(self, _id: str) -> _BIN:
        _r = await self.__get(_id, {"Accept": "application/json"})
        if _r[0] == 200:
            self.__bins[_id] = self._BIN(
                _r[1], self.__get, self.__post, self.__put, self.__delete)
        elif _r[0] == 404:
            raise InvalidBin(_id)
        return self.__bins[_id]
